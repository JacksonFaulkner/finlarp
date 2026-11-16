"""Detailed gate-all-around parts and the GATE-ALL-AROUND page's sections 1-10 (chip_gaa.py calls
sec1..sec10).

A section is a close-up of a nanosheet transistor row, drawn to scale (NM units per nm): three
silicon sheets ~6 nm thick, ~10 nm apart and ~30 nm wide, stacked on a silicon mesa in the STI
oxide; the high-k and work-function metal fill every gap between the sheets, nitride inner
spacers sit between the gate and the source/drain epi at each level, a nitride gate spacer and
cap above, tungsten trench contacts on the epi. The same builder draws the process steps
(superlattice, dummy gate, release), the n/p pair, the forksheet wall and the CFET stack.

Coordinates and cut-aways are those of chip_finfet_detail.py: the channel runs along x, the
sheet width is along z, and `cut_mode` clips every part as it is built.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat, box, disc, empty, label, pivot, rel, show, tube  # noqa: E402
from sand_zooms import scale_keys, stream_of  # noqa: E402
from chip_kit import glide_camera, route  # noqa: E402
import chip_finfet_detail as D  # noqa: E402
import chip_kit as C  # noqa: E402
from chip_finfet_detail import (  # noqa: E402
    CAP, EPS, FIN_BOT, HK, SUB_BOT, cbox, cprism, cut_mode, pose, save, scene, sd_spans, turn, turned, wafer,
)

TS, TG = 60.0, 100.0  # sheet thickness ~6 nm, gap ~10 nm
GL, GP, SP = 150.0, 450.0, 60.0  # gate length ~15 nm, gate pitch ~45 nm, spacer ~6 nm
W = 300.0  # sheet width ~30 nm
WF = 30.0
ISO = 180.0  # CFET: the extra gap between the lower and the upper stack
MESA_BOT = FIN_BOT
EPI_TOP_PAD = 80.0


def sheet_y(k, cfet=False):
    lo = TG + k * (TS + TG) + (ISO if cfet and k >= 3 else 0.0)
    return lo, lo + TS


def gaa(parent, m, name, w=W, ns=3, gates=(-GP, 0.0, GP), gl=GL, sp=SP, gp=GP, dz=0.0, lanes=None,
        parts=("sub", "sti", "mesa", "sheets", "spacer", "epi", "gate", "contact"), cfet=False, wall=None):
    """A nanosheet row. `lanes` is a list of (z0, z1, pmos) sheet stacks side by side (default one
    n stack `w` wide at `dz`). Parts:
      sub, sti, mesa       substrate, oxide, the silicon mesa under each stack
      stack                the superlattice: Si sheets and SiGe layers the full length (no gates)
      sheets               Si sheets cut to each gate (from epi to epi)
      sige                 SiGe left under each gate (before release)
      dummy                the placeholder poly gate
      spacer               gate spacers, inner spacers and the cap line
      epi, gate, contact   S/D epi, the HK/metal gate with its cap, trench contacts
    `wall` (half-thickness) puts a forksheet wall at z = dz. `cfet` stacks 3 p sheets under 3 n
    sheets (ns = 6). Returns a dict of group empties and the extents."""
    g = empty(name, parent)
    if lanes is None:
        lanes = [(dz - w / 2, dz + w / 2, False)]
    if cfet:
        ns = 6
    top = sheet_y(ns - 1, cfet)[1]
    gtop = top + 220.0
    zl, zr = min(a for a, _, _ in lanes) - 100.0, max(b for _, b, _ in lanes) + 100.0
    spans = sd_spans(gates, gl, sp, gp)
    xa, xb = spans[0][0], spans[-1][1]
    grp = {}

    def group(k):
        if k not in grp:
            grp[k] = empty(f"{name}_{k}", g)
        return grp[k]

    if "sub" in parts:
        cbox(f"{name}_sub", (xa, SUB_BOT, zl - 40), (xb, MESA_BOT, zr + 40), m["d_sub"], group("sub"), 1)
    if "sti" in parts:
        cbox(f"{name}_sti", (xa, MESA_BOT, zl - 40), (xb, 0.0, zr + 40), m["d_sti"], group("sti"), 1)
    for li, (za, zb, pm) in enumerate(lanes):
        if "mesa" in parts:
            cbox(f"{name}_mesa{li}", (xa - 2, MESA_BOT, za), (xb + 2, 0.0, zb), m["d_si"], group("mesa"), 4)
        for k in range(ns):
            y0, y1 = sheet_y(k, cfet)
            if "stack" in parts:
                cbox(f"{name}_ss{li}_{k}", (xa, y0, za), (xb, y1, zb), m["d_si"], group("stack"), 6)
                gy0 = y0 - TG
                cbox(f"{name}_sg{li}_{k}", (xa, gy0, za), (xb, y0, zb), m["d_sige"], group("stack"), 5)
            for i, gx in enumerate(gates):
                if "sheets" in parts:
                    cbox(f"{name}_s{li}_{i}_{k}", (gx - gl / 2 - sp, y0, za), (gx + gl / 2 + sp, y1, zb), m["d_si"],
                         group("sheets"), 6)
                if "sige" in parts:
                    cbox(f"{name}_sige{li}_{i}_{k}", (gx - gl / 2, y0 - TG, za), (gx + gl / 2, y0, zb), m["d_sige"],
                         group("sige"), 5)
                if "spacer" in parts:  # inner spacers: the ends of each gap, by the epi
                    for s in (-1, 1):
                        a, b = sorted((gx + s * gl / 2, gx + s * (gl / 2 + sp)))
                        cbox(f"{name}_isp{li}_{i}_{k}{s:+d}", (a, y0 - TG, za), (b, y0, zb), m["d_nit"], group("spacer"), 5)
                if "gate" in parts:
                    cbox(f"{name}_hk{li}_{i}_{k}", (gx - gl / 2, y0 - HK, za - HK), (gx + gl / 2, y1 + HK, zb + HK),
                         m["d_hk"], group("hk"), 3)
        if cfet and "spacer" in parts:  # the isolation between the two stacks, by the epi
            for i, gx in enumerate(gates):
                for s_ in (-1, 1):
                    a, b = sorted((gx + s_ * gl / 2, gx + s_ * (gl / 2 + sp)))
                    cbox(f"{name}_iso_sp{li}_{i}{s_:+d}", (a, sheet_y(2, True)[1], za), (b, sheet_y(3, True)[0] - TG, zb),
                         m["d_nit"], group("spacer"), 5)
    if "stack" in parts:
        # the hard mask the fin was etched with, on the top sheet
        for li, (za, zb, pm) in enumerate(lanes):
            cbox(f"{name}_hm{li}", (xa, top, za), (xb, top + 70, zb), m["d_nit"], group("stack"), 5)
    if wall is not None:
        cbox(f"{name}_wall", (xa, MESA_BOT, dz - wall), (xb, gtop, dz + wall), m["d_nit"], group("wall"), 7)
    for i, gx in enumerate(gates):
        x0, x1 = gx - gl / 2, gx + gl / 2
        if "dummy" in parts:
            cbox(f"{name}_dum{i}", (x0, 0.0, zl), (x1, gtop, zr), m["d_poly"], group("dummy"), 1)
        if "spacer" in parts:
            for s in (-1, 1):
                a, b = sorted((gx + s * gl / 2, gx + s * (gl / 2 + sp)))
                cbox(f"{name}_osp{i}{s:+d}", (a, top, zl), (b, gtop + CAP, zr), m["d_nit"], group("spacer"), 1)
                # beside the stacks, down to the oxide
                edges = [zl] + [v for za, zb, _ in lanes for v in (za, zb)] + [zr]
                for j in range(0, len(edges), 2):
                    cbox(f"{name}_osp{i}{s:+d}_{j}", (a, 0.0, edges[j]), (b, top, edges[j + 1]), m["d_nit"],
                         group("spacer"), 1)
        if "gate" in parts:
            cbox(f"{name}_wfm{i}", (x0, 0.0, zl), (x1, gtop, zr), m["d_wfm"], group("wfm"), 1)
            cbox(f"{name}_fill{i}", (x0, top + HK + WF, zl + WF), (x1, gtop + 2, zr - WF), m["d_fill"], group("fill"), 2)
            cbox(f"{name}_hkb{i}", (x0 + 3, 0.0, zl + 3), (x1 - 3, HK, zr - 3), m["d_hk"], group("hk"), 3)
            cbox(f"{name}_cap{i}", (x0, gtop, zl), (x1, gtop + CAP, zr), m["d_nit"], group("cap"), 1)
    ept = top + EPI_TOP_PAD
    for j, (a, b) in enumerate(spans):
        for li, (za, zb, pm) in enumerate(lanes):
            wz = zb - za
            zc = (za + zb) / 2
            if "epi" in parts:
                def poly(ylo, yhi, o=70.0):
                    return [(za, ylo), (zb, ylo), (zb + o, ylo + 0.55 * (yhi - ylo)), (zc + wz * 0.38, yhi),
                            (zc - wz * 0.38, yhi), (za - o, ylo + 0.55 * (yhi - ylo))]
                if wall is not None:  # the epi stops at the wall
                    def poly(ylo, yhi, o=70.0, za=za, zb=zb):  # noqa: F811
                        near = zb if zb <= dz else za
                        far = za if zb <= dz else zb
                        s = -1 if zb <= dz else 1
                        return [(near, ylo), (far, ylo), (far + s * o, ylo + 0.55 * (yhi - ylo)),
                                (far - s * 0.2 * wz, yhi), (near, yhi)]
                if cfet:
                    ymid = sheet_y(2, True)[1] + 50
                    cprism(f"{name}_pe{j}_{li}", poly(-60.0, ymid), "x", a, b, m["d_pepi"], group("epi"), 5)
                    cbox(f"{name}_iso{j}_{li}", (a, ymid, za - 40), (b, ymid + 60, zb + 40), m["d_nit"], group("epi"), 5)
                    cprism(f"{name}_ne{j}_{li}", poly(ymid + 60, ept), "x", a, b, m["d_nepi"], group("epi"), 5)
                else:
                    cprism(f"{name}_epi{j}_{li}", poly(-60.0, ept), "x", a, b, m["d_pepi"] if pm else m["d_nepi"],
                           group("epi"), 5)
            if "contact" in parts:
                cbox(f"{name}_ct{j}_{li}", (a + 22, ept - 30, za + 15), (b - 22, gtop + CAP, zb - 15), m["d_w"],
                     group("contact"), 2)
    grp["_ext"] = (xa, xb, zl, zr, top, gtop, spans)
    return grp


def chan_glow(parent, m, name, gx, ns=3, z1=10.0, w=W, cfet=False):
    g = empty(name, parent)
    for k in range(ns):
        y0, y1 = sheet_y(k, cfet)
        cbox(f"{name}{k}", (gx - GL / 2 - SP, y0 - 3, -w / 2), (gx + GL / 2 + SP, y1 + 3, z1), m["d_chan"], g, 8)
    return g


def scene_g(name, beats):
    return scene(name, beats)


QUAD_YAW, QUAD_PITCH = -0.85, 0.32  # three-quarter view onto a "quadl" cut
FRONT = 0.16  # near-front yaw, onto a "z" cut or a turned "x" cut
Y_TOP = sheet_y(2)[1]  # 480
GTOP = Y_TOP + 220.0
ONE = {"gates": (0.0,), "gp": 640.0}  # one transistor: source, one gate, drain
SRC_X = -(GL / 2 + SP + (640.0 - GL - 2 * SP) / 4)  # the middle of the source epi in ONE
GY = sheet_y(1)[0] - TG / 2  # the middle of the gap under the middle sheet


# ---- sections ----------------------------------------------------------------------------------


def sec1():
    """1, what happens: the Si/SiGe fin, the released sheets, the gate wrapped round them."""
    name = "gaa_sec1"
    m, root = scene_g(name, 3)
    cut_mode("quadl", x=0.0, z=0.0)
    b0, b1, b2 = (empty(f"b{i}", root) for i in range(3))
    gaa(b0, m, "sl", parts=("sub", "sti", "mesa", "stack"), **ONE)
    gaa(b1, m, "rel", parts=("sub", "sti", "mesa", "sheets", "spacer", "epi"), **ONE)
    gaa(b2, m, "hkmg", parts=("sub", "sti", "mesa", "sheets", "spacer", "epi", "gate", "contact"), **ONE)
    for i, b in enumerate((b0, b1, b2)):
        show(b, beat(i))
    label("Si sheet", (-200.0, sheet_y(2)[0] + TS / 2, 0.0), root, beat(0))
    label("SiGe (sacrificial)", (-200.0, GY, 0.0), root, beat(0))
    label("etched into a fin", (0.0, Y_TOP + 70, W / 2), root, beat(0))
    label("SiGe gone: sheets float", (0.0, GY, 60.0), root, beat(1))
    label("S/D epi holds the ends", (SRC_X, 300.0, 0.0), root, beat(1))
    label("inner spacer", (-(GL / 2 + SP / 2), sheet_y(0)[0] - TG / 2, 0.0), root, beat(1))
    label("gate on all 4 sides", (0.0, sheet_y(2)[1], W / 4), root, beat(2))
    label("high-k + metal in the gaps", (-GL / 4, GY, 0.0), root, beat(2))
    label("trench contact", (SRC_X, GTOP + CAP, 0.0), root, beat(2))
    t = (0.0, 150.0, 0.0)
    glide_camera(root, [pose(t, 2700.0, QUAD_YAW, QUAD_PITCH), pose(t, 2650.0, QUAD_YAW, QUAD_PITCH),
                        pose(t, 2700.0, QUAD_YAW, QUAD_PITCH)])
    save(name)


def sec2():
    """2, along the channel: source epi, sheets, drain epi; the current; spacers and the bottom."""
    name = "gaa_sec2"
    m, root = scene_g(name, 3)
    cut_mode("z", z=0.0)
    gaa(root, m, "row", gates=(-GP, 0.0, GP))
    show(chan_glow(root, m, "glow", 0.0), beat(1))
    ycs = [sum(sheet_y(k)) / 2 for k in range(3)]
    s_x, d_x = -GP / 2, GP / 2
    for k, yc in enumerate(ycs):
        s, p = route([(s_x, yc, 24.0), (d_x, yc, 24.0)])
        stream_of(root, f"e{k}", 8, s, p, 14.0, m["c_dot_sig"], 1, 0.05, 0.7, 70)
    pts = empty("pts", root)
    cbox("pts_band", (-GP * 1.5 - 90, -200.0, -W / 2), (GP * 1.5 + 90, -110.0, 12.0), m["d_pts"], pts, 8)
    show(pts, beat(2))
    label("source epi (SiP)", (s_x, 420.0, 0.0), root, beat(0))
    label("drain epi", (d_x, 420.0, 0.0), root, beat(0))
    label("3 Si nanosheets", (0.0, ycs[2], 0.0), root, beat(0))
    label("gate, nitride cap on top", (0.0, GTOP + CAP / 2, 0.0), root, beat(0))
    label("electrons in every sheet", (-40.0, ycs[1], 0.0), root, beat(1))
    label("source", (s_x, -30.0, 0.0), root, beat(1))
    label("drain", (d_x, -30.0, 0.0), root, beat(1))
    label("inner spacer (SiN)", (GL / 2 + SP / 2, GY, 0.0), root, beat(2))
    label("gate metal between sheets", (0.0, GY, 0.0), root, beat(2))
    label("punch-through stop", (-GP, -155.0, 0.0), root, beat(2))
    glide_camera(root, [pose((0.0, 200.0, 0.0), 2900.0, FRONT, 0.10), pose((0.0, 280.0, 0.0), 1900.0, FRONT, 0.08),
                        pose((0.0, 160.0, 0.0), 2500.0, FRONT, 0.10)])
    save(name)


def sige_shrink(parent, m, name, gx, z1, b):
    """The SiGe under one gate, each layer etched from both ends to nothing during beat `b`."""
    g = empty(name, parent)
    for k in range(3):
        y0 = sheet_y(k)[0]
        at = (gx, y0 - TG / 2, (-W / 2 + z1) / 2)
        pv = pivot(f"{name}{k}", at, g)
        box(f"{name}{k}_b", rel(at, (gx - GL / 2, y0 - TG, -W / 2)), rel(at, (gx + GL / 2, y0, z1)), m["d_sige"], pv)
        scale_keys(pv, [(F(b, 0.12), (1, 1, 1)), (F(b, 0.7), (0.02, 1, 1))])
    return g


def release_scene(name="gaa_sec3"):
    """3, before and after release: SiGe in the gaps; etched out sideways; metal in its place."""
    m, root = scene_g(name, 3)
    cut_mode("z", z=0.0)
    b0, b1, b2 = (empty(f"b{i}", root) for i in range(3))
    gaa(b0, m, "pre", parts=("sub", "sti", "mesa", "sheets", "sige", "dummy", "spacer", "epi"), **ONE)
    gaa(b1, m, "rel", parts=("sub", "sti", "mesa", "sheets", "spacer", "epi"), **ONE)
    sige_shrink(b1, m, "sg_", 0.0, EPS * 5, 1)
    gaa(b2, m, "post", parts=("sub", "sti", "mesa", "sheets", "spacer", "epi", "gate"), **ONE)
    for i, b in enumerate((b0, b1, b2)):
        show(b, beat(i))
    label("SiGe between the sheets", (0.0, GY, 0.0), root, beat(0))
    label("dummy poly gate", (0.0, GTOP - 60, 0.0), root, beat(0))
    label("inner spacer (nitride)", (GL / 2 + SP / 2, sheet_y(0)[0] - TG / 2, 0.0), root, beat(0))
    label("SiGe etched sideways", (0.0, GY, 0.0), root, beat(1))
    label("Si sheets must survive", (-GL / 2, sheet_y(2)[0] + TS / 2, 0.0), root, beat(1))
    label("dummy gate gone", (0.0, GTOP - 60, 0.0), root, beat(1))
    label("high-k (yellow) + metal", (0.0, GY, 0.0), root, beat(2))
    label("source epi", (SRC_X, 300.0, 0.0), root, beat(2))
    t = (0.0, 230.0, 0.0)
    glide_camera(root, [pose(t, 2300.0, FRONT, 0.10)] * 3)
    save(name)


def sec4():
    """4, the new process modules, one per beat: superlattice, inner spacer, epi, release, gate."""
    name = "gaa_sec4"
    m, root = scene_g(name, 5)
    cut_mode("quadl", x=0.0, z=0.0)
    stages = [
        ("sub", "sti", "mesa", "stack"),
        ("sub", "sti", "mesa", "sheets", "sige", "dummy", "spacer"),
        ("sub", "sti", "mesa", "sheets", "sige", "dummy", "spacer", "epi"),
        ("sub", "sti", "mesa", "sheets", "spacer", "epi"),
        ("sub", "sti", "mesa", "sheets", "spacer", "epi", "gate"),
    ]
    for i, parts in enumerate(stages):
        b = empty(f"b{i}", root)
        gaa(b, m, f"st{i}", parts=parts, **ONE)
        show(b, beat(i))
    label("SUPERLATTICE: Si / SiGe", (-200.0, GY, 0.0), root, beat(0))
    label("hard mask", (200.0, Y_TOP + 70, W / 2), root, beat(0))
    label("DUMMY GATE (poly)", (0.0, GTOP, W / 2 + 100), root, beat(1))
    label("INNER SPACER: SiGe recessed", (-(GL / 2 + SP / 2), GY, 0.0), root, beat(1))
    label("S/D EPI from the sheet ends", (SRC_X, Y_TOP, 0.0), root, beat(2))
    label("RELEASE: SiGe etched out", (-GL / 4, GY, 0.0), root, beat(3))
    label("dummy gate removed", (0.0, Y_TOP + 60, W / 2 + 100), root, beat(3))
    label("HK/METAL GATE by ALD", (-GL / 4, GY, 0.0), root, beat(4))
    t = (0.0, 150.0, 0.0)
    glide_camera(root, [pose(t, 2700.0, QUAD_YAW, QUAD_PITCH)] * 5)
    save(name)


def width_scene(name="gaa_sec5"):
    """5, sheet width: FinFET whole fins, a wide sheet stack, a narrow one (cut across the gate)."""
    m, root = scene_g(name, 3)
    cut_mode("x", x=0.0)
    b0, b1, b2 = (turned(root, f"b{i}") for i in range(3))
    D.finfet(b0, m, "fins", n=2, parts=("sub", "sti", "fins", "gate", "spacer"), **ONE)
    gaa(b1, m, "wide", w=500.0, parts=("sub", "sti", "mesa", "sheets", "spacer", "gate"), **ONE)
    gaa(b2, m, "narrow", w=150.0, parts=("sub", "sti", "mesa", "sheets", "spacer", "gate"), **ONE)
    label("FinFET: 1 fin, 2 fins, never 1.5", (0.0, D.FH, -D.FP / 2), b0, beat(0))
    label("fin ~7 nm wide", (0.0, D.FH * 0.6, D.FP / 2), b0, beat(0))
    label("wide sheets ~50 nm: drive", (0.0, sheet_y(2)[0] + TS / 2, 0.0), b1, beat(1))
    label("same 3-sheet height", (0.0, sheet_y(0)[0] + TS / 2, -200.0), b1, beat(1))
    label("narrow ~15 nm: low leakage", (0.0, sheet_y(2)[0] + TS / 2, 0.0), b2, beat(2))
    label("smaller cell", (0.0, GTOP, -75.0), b2, beat(2))
    for b in (b0, b1, b2):
        turn(b)
    for i, b in enumerate((b0, b1, b2)):
        show(b, beat(i))
    t = (0.0, 200.0, 0.0)
    glide_camera(root, [pose(t, 2600.0, FRONT, 0.10)] * 3)
    save(name)


def power_scene(name="gaa_sec6"):
    """6, backside power: power on the front with the signals; rails under the device; signals only."""
    m, root = scene_g(name, 3)
    cut_mode("z", z=0.0)
    gaa(root, m, "row", gates=(-GP, 0.0, GP), parts=("sti", "mesa", "sheets", "spacer", "epi", "gate", "contact"))
    xa, xb = -GP * 1.5 - 90, GP * 1.5 + 90
    za, zb = -W / 2 - 140, W / 2 + 140
    sub = empty("sub", root)
    cbox("sub_bulk", (xa, SUB_BOT, za), (xb, MESA_BOT, zb), m["d_sub"], sub, 1)
    show(sub, beat(0))
    y0 = GTOP + CAP + 120.0
    xs = -GP / 2 - GP  # the left source
    cbox("ild", (xa, GTOP + CAP, za), (xb, y0 + 640, -60.0), m["d_sti"], root, 0)
    front = empty("front", root)
    cbox("rail_front", (xa, y0 + 480, -260.0), (xb, y0 + 600, 0.0), m["d_gold"], front, 2)
    cbox("pv_front", (xs - 30, GTOP + CAP, -120.0), (xs + 30, y0 + 480, 0.0), m["d_gold"], front, 3)
    show(front, beat(0))
    sig = empty("sig", root)
    lines = ((-560.0, -120.0, y0), (120.0, 900.0, y0), (-500.0, 500.0, y0 + 240))
    for k, (x0, x1, y) in enumerate(lines):
        cbox(f"m{k}", (x0, y, -200.0), (x1, y + 70.0, 0.0), m["d_cu"], sig, 2)
    for k, x in enumerate((GP / 2 + GP, GP / 2)):
        cbox(f"v{k}", (x - 30, GTOP + CAP, -120.0), (x + 30, y0, 0.0), m["d_cu"], sig, 2)
    sig_lit = empty("sig_lit", root)
    for k, (x0, x1, y) in enumerate(lines):
        cbox(f"ml{k}", (x0 - 4, y - 4, -204.0), (x1 + 4, y + 74.0, 4.0), m["d_hl3"], sig_lit, 4)
    show(sig_lit, beat(2))
    back = empty("back", root)
    cbox("bs_ild", (xa, MESA_BOT - 200, za), (xb, MESA_BOT, zb), m["d_sti"], back, 1)
    cbox("rail_back", (xa, MESA_BOT - 360, za), (xb, MESA_BOT - 200, zb), m["d_gold"], back, 2)
    cbox("ntsv", (xs - 40, MESA_BOT - 200, -50.0), (xs + 40, -40.0, 50.0), m["d_gold"], back, 9)
    show(back, [(F(1, 0), F(3, 0))])
    s, p = route([(xs, y0 + 540, 24.0), (xs, 300.0, 24.0)])
    stream_of(root, "pw0", 8, s, p, 20.0, m["c_dot_vdd"], 0, 0.05, 0.7, 80)
    s, p = route([(xs, MESA_BOT - 280, 60.0), (xs, 300.0, 60.0)])
    stream_of(root, "pw1", 8, s, p, 20.0, m["c_dot_vdd"], 1, 0.05, 0.7, 80)
    s, p = route([(-560.0, y0 + 35, 24.0), (-120.0, y0 + 35, 24.0)])
    stream_of(root, "sg2", 6, s, p, 16.0, m["c_dot_sig"], 2, 0.05, 0.7, 60)
    label("power rail on the front", (-700.0, y0 + 600, 0.0), root, beat(0))
    label("signal wires squeezed", (300.0, y0 + 70, 0.0), root, beat(0))
    label("silicon substrate", (-700.0, -420.0, 0.0), root, beat(0))
    label("power rail on the back", (-700.0, MESA_BOT - 280, 0.0), root, beat(1))
    label("nano-TSV to the source", (xs, MESA_BOT - 100, 40.0), root, beat(1))
    label("wafer thinned, flipped", (500.0, MESA_BOT - 100, 0.0), root, beat(1))
    label("front metal: signals only", (300.0, y0 + 70, 0.0), root, beat(2))
    label("Intel 18A PowerVia, TSMC A16", (-700.0, MESA_BOT - 280, 0.0), root, beat(2))
    t = (0.0, 330.0, 0.0)
    glide_camera(root, [pose(t, 4800.0, FRONT, 0.10), pose((0.0, 200.0, 0.0), 4300.0, FRONT, 0.10),
                        pose(t, 4800.0, FRONT, 0.10)])
    save(name)


def backside(parent, m, name, xa, xb, za, zb):
    """A thinned wafer's back: backside dielectric and a power rail under the mesas."""
    cbox(f"{name}_bs", (xa, MESA_BOT - 200, za), (xb, MESA_BOT, zb), m["d_sti"], parent, 1)
    cbox(f"{name}_rail", (xa, MESA_BOT - 340, za), (xb, MESA_BOT - 200, zb), m["d_gold"], parent, 2)


def sec7():
    """7, node comparison: Samsung SF3E wide sheets; TSMC N2 and Intel 18A; A16 backside contact."""
    name = "gaa_sec7"
    m, root = scene_g(name, 3)
    cut_mode("quadl", x=0.0, z=0.0)
    b0 = empty("b0", root)
    gaa(b0, m, "sf3", w=480.0, **ONE)
    label("Samsung SF3E, 2022: first GAA", (SRC_X, GTOP + CAP, 0.0), b0, beat(0))
    label("MBCFET: wide sheets", (0.0, sheet_y(2)[1], 120.0), b0, beat(0))
    show(b0, beat(0))
    cut_mode("x", x=0.0)
    b1 = turned(root, "b1")
    gaa(b1, m, "n2", dz=-330.0, parts=("sub", "sti", "mesa", "sheets", "spacer", "gate"), **ONE)
    gaa(b1, m, "i18", ns=4, dz=330.0, parts=("sti", "mesa", "sheets", "spacer", "gate"), **ONE)
    backside(b1, m, "i18", -320.0, 0.0, 330.0 - W / 2 - 140, 330.0 + W / 2 + 140)
    label("TSMC N2: 3 sheets, 4Q25", (0.0, sheet_y(2)[0] + TS / 2, -330.0), b1, beat(1))
    label("Intel 18A: 4 ribbons, 2025", (0.0, sheet_y(3)[0] + TS / 2, 330.0), b1, beat(1))
    label("PowerVia rail below", (0.0, MESA_BOT - 270, 330.0), b1, beat(1))
    turn(b1)
    show(b1, beat(1))
    cut_mode("z", z=0.0)
    b2 = empty("b2", root)
    gaa(b2, m, "a16", parts=("sti", "mesa", "sheets", "spacer", "epi", "gate", "contact"), **ONE)
    backside(b2, m, "a16", -320.0, 320.0, -W / 2 - 140, W / 2 + 140)
    cbox("a16_bc", (SRC_X - 40, MESA_BOT - 200, -50.0), (SRC_X + 40, -40.0, 50.0), m["d_gold"], b2, 9)
    s, p = route([(SRC_X, MESA_BOT - 280, 60.0), (SRC_X, 300.0, 60.0)])
    stream_of(b2, "pw", 8, s, p, 18.0, m["c_dot_vdd"], 2, 0.05, 0.7, 80)
    label("TSMC A16, 2026+", (0.0, GTOP + CAP, 0.0), b2, beat(2))
    label("Super Power Rail", (200.0, MESA_BOT - 270, 0.0), b2, beat(2))
    label("source fed from below", (SRC_X, MESA_BOT - 100, 40.0), b2, beat(2))
    show(b2, beat(2))
    glide_camera(root, [
        pose((0.0, 150.0, 0.0), 3000.0, QUAD_YAW, QUAD_PITCH),
        pose((0.0, 150.0, 0.0), 3000.0, FRONT, 0.10),
        pose((0.0, 150.0, 0.0), 3000.0, FRONT, 0.10),
    ], glide=0.15)
    save(name)


def sec8():
    """8, roadmap: an n/p nanosheet pair, the forksheet wall between them, then the CFET stack."""
    name = "gaa_sec8"
    m, root = scene_g(name, 3)
    cut_mode("x", x=0.0)
    parts = ("sub", "sti", "mesa", "sheets", "spacer", "gate", "epi")
    b0, b1, b2 = (turned(root, f"b{i}") for i in range(3))
    gaa(b0, m, "pair", parts=parts, lanes=[(-500.0, -200.0, False), (200.0, 500.0, True)], **ONE)
    gaa(b1, m, "fork", parts=parts, lanes=[(-340.0, -40.0, False), (40.0, 340.0, True)], wall=40.0, **ONE)
    gaa(b2, m, "cfet", parts=parts, cfet=True, **ONE)
    label("nFET sheets", (0.0, sheet_y(2)[0] + TS / 2, -350.0), b0, beat(0))
    label("pFET sheets", (0.0, sheet_y(2)[0] + TS / 2, 350.0), b0, beat(0))
    label("n-p gap: lost width", (0.0, 120.0, 0.0), b0, beat(0))
    label("forksheet: dielectric wall", (0.0, GTOP - 60, 0.0), b1, beat(1))
    label("imec: to ~A10", (0.0, sheet_y(1)[0] + TS / 2, 190.0), b1, beat(1))
    label("CFET: nFET on top", (0.0, sheet_y(4, True)[0] + TS / 2, 0.0), b2, beat(2))
    label("pFET stack below", (0.0, sheet_y(1, True)[0] + TS / 2, 0.0), b2, beat(2))
    label("imec: ~A7, after 2030", (0.0, sheet_y(5, True)[1] + 220 + CAP, -150.0), b2, beat(2))
    for b in (b0, b1, b2):
        turn(b)
    for i, b in enumerate((b0, b1, b2)):
        show(b, beat(i))
    glide_camera(root, [
        pose((0.0, 200.0, 0.0), 2800.0, FRONT, 0.10),
        pose((0.0, 200.0, 0.0), 2600.0, FRONT, 0.10),
        pose((0.0, 460.0, 0.0), 3900.0, FRONT, 0.10),
    ])
    save(name)


def sec9():
    """9, yield and cost: a wafer at ~55% good dies, one at ~84%, then the reported wafer prices."""
    name = "gaa_sec9"
    m, root = scene_g(name, 3)
    b0, b1, b2 = (empty(f"b{i}", root) for i in range(3))
    wafer(b0, m, "sf3", (0.0, 0.0, 0.0), 760.0, 0.55, 3)
    wafer(b1, m, "n3e", (0.0, 0.0, 0.0), 760.0, 0.84, 5)
    wafer(b2, m, "w3", (-520.0, 0.0, 0.0), 420.0, 1.0, 1, die=90.0)
    wafer(b2, m, "w2", (520.0, 0.0, 0.0), 420.0, 1.0, 1, die=90.0)
    for i, (x, k) in enumerate(((-520.0, 18), (520.0, 30))):
        for j in range(k):
            disc(f"coin{i}_{j}", (x + 300.0, 30.0 + j * 26 + 12, -420.0), 120.0, 22.0, m["d_gold"], b2, verts=32)
    for i, b in enumerate((b0, b1, b2)):
        show(b, beat(i))
    label("Samsung SF3E: ~50-60% (reports)", (-760.0, 20.0, 0.0), root, beat(0))
    label("red: failed die", (0.0, 20.0, 0.0), root, beat(0))
    label("TSMC N3E FinFET: ~82-86%", (-760.0, 20.0, 0.0), root, beat(1))
    label("N3: ~$18k a wafer (reported)", (-220.0, 30.0 + 18 * 26, -420.0), root, beat(2))
    label("N2: >$30k (reported)", (820.0, 30.0 + 30 * 26, -420.0), root, beat(2))
    glide_camera(root, [pose((0.0, 0.0, 0.0), 3100.0, 0.0, 0.95), pose((0.0, 0.0, 0.0), 3100.0, 0.0, 0.95),
                        pose((150.0, 280.0, -100.0), 3300.0, 0.0, 0.45)], glide=0.15)
    save(name)


def sec10():
    """10, sources: the finished row, the camera turning round it, a source pinned to each part."""
    name = "gaa_sec10"
    m, root = scene_g(name, 4)
    cut_mode("quadl", x=0.0, z=0.0)
    gaa(root, m, "row")
    label("Samsung 3GAA [1]", (0.0, sheet_y(2)[1], W / 4), root, beat(0))
    label("Intel 18A, PowerVia [2]", (GP, GTOP + CAP, 0.0), root, beat(0))
    label("TSMC N2 [3], A16 [4]", (-GP / 2, Y_TOP + 80, 0.0), root, beat(1))
    label("forksheet, CFET: imec [5]", (-GP, GTOP + CAP, 0.0), root, beat(1))
    label("yields, wafer prices [6]", (GP / 2, 300.0, W / 2), root, beat(2))
    label("Applied GAA spend [7]", (0.0, GTOP + CAP, -W / 2), root, beat(2))
    label("Lam Akara etch [8]", (-GP / 2, 300.0, 0.0), root, beat(3))
    label("SiGe selective etch [9]", (-GL / 4, GY, 0.0), root, beat(3))
    t = (0.0, 150.0, 0.0)
    glide_camera(root, [pose(t, 3300.0, -0.45, 0.36), pose(t, 3200.0, -0.70, 0.32), pose(t, 3300.0, -0.95, 0.30),
                        pose(t, 3200.0, -0.70, 0.40)], glide=0.6)
    save(name)


def sec3():
    release_scene()


def sec5():
    width_scene()


def sec6():
    power_scene()


SECTIONS = [sec1, sec2, sec3, sec4, sec5, sec6, sec7, sec8, sec9, sec10]


# ---- overview and zoom-ins -------------------------------------------------------------------

CT_X = GL / 2 + SP + (640.0 - GL - 2 * SP) / 4  # the source and drain contacts' x in ONE


def sheet_path(k, z=24.0):
    """Source contact top, down the source epi, along sheet `k`, up the drain epi to its contact."""
    yc = sum(sheet_y(k)) / 2
    return [(-CT_X, GTOP + CAP, z), (-CT_X, Y_TOP + 40, z), (-GL / 2 - SP, yc, z), (GL / 2 + SP, yc, z),
            (CT_X, Y_TOP + 40, z), (CT_X, GTOP + CAP, z)]


def overview():
    """The overview: the whole chip; in on the stack; the gate wraps the sheets; current through
    every sheet; a wide sheet; a narrow sheet; back out to the whole chip."""
    m, root = scene_g("gaa", 7)
    rest = D.chip_rest(root, m)
    show(rest, [(0, F(1, 0.25)), (F(6, 0), F(7, 0))])
    dev = ("sheets", "spacer", "epi", "gate", "contact")
    cut_mode("z", z=0.0)
    o, k = D.placed(root, "dev_whole")
    gaa(k, m, "w", parts=dev, **ONE)
    hl = empty("hl", k)
    cbox("hl_box", (-340.0, -60.0, -280.0), (340.0, GTOP + CAP + 40, 30.0), m["d_hlbox"], hl, 9)
    show(hl, [(0, F(1, 0))])
    label("GAA transistor (the NMOS)", (0.0, GTOP + CAP + 40, 0.0), k, [(0, F(1, 0))])
    label("back to the whole chip", (0.0, GTOP + CAP + 40, 0.0), k, [(F(6, 0.1), F(7, 0))])
    show(o, [(0, F(1, 0)), (F(6, 0), F(7, 0))])
    # beat 1: along the channel
    o1, k1 = D.placed(root, "stack")
    gaa(k1, m, "s", parts=dev, **ONE)
    label("source epi", (-CT_X, 300.0, 0.0), k1, beat(1))
    label("drain epi", (CT_X, 300.0, 0.0), k1, beat(1))
    label("3 Si nanosheets", (0.0, sheet_y(2)[0] + TS / 2, 0.0), k1, beat(1))
    label("gate metal between sheets", (0.0, GY, 0.0), k1, beat(1))
    show(o1, beat(1))
    # beat 2: the gate round every sheet (cut across the gate and along the sheets)
    cut_mode("quadl", x=0.0, z=0.0)
    o2, k2 = D.placed(root, "wrap")
    gaa(k2, m, "q", parts=dev, **ONE)
    label("gate on all 4 sides", (0.0, sheet_y(2)[1], W / 4), k2, beat(2))
    label("high-k (yellow) + metal", (-GL / 4, GY, 0.0), k2, beat(2))
    show(o2, beat(2))
    # beat 3: current through every sheet
    cut_mode("z", z=0.0)
    o3, k3 = D.placed(root, "on")
    gaa(k3, m, "c", parts=dev, **ONE)
    chan_glow(k3, m, "glow", 0.0)
    for s in range(3):
        D.ride(k3, f"e{s}", sheet_path(s), 6, 14.0, m["c_dot_sig"], 3, 0.05 + 0.08 * s, 0.7 + 0.08 * s, 100)
    label("electrons in all 3 sheets", (0.0, sheet_y(1)[0] + TS / 2, 0.0), k3, beat(3))
    label("source contact", (-CT_X, GTOP + CAP, 0.0), k3, beat(3))
    show(o3, beat(3))
    # beats 4 and 5: wide and narrow sheets, cut across the gate
    cut_mode("x", x=0.0)
    for b, (w, tag, note) in enumerate(((500.0, "wide", "wide sheet: more drive"), (150.0, "narrow", "narrow: less leakage")), 4):
        ob, kb = D.placed(root, tag)
        t = turned(kb, f"{tag}_t")
        gaa(t, m, tag, w=w, parts=("sheets", "spacer", "gate"), **ONE)
        label(note, (0.0, sheet_y(2)[0] + TS / 2, 0.0), t, beat(b))
        label("same stack height", (0.0, sheet_y(0)[0] + TS / 2, -w / 2), t, beat(b))
        turn(t)
        show(ob, beat(b))
    cx = C.NMOS_X
    glide_camera(root, [
        C.WHOLE,
        pose((cx, 140.0, 0.0), 900.0, FRONT, 0.10),
        pose((cx, 130.0, 0.0), 1050.0, QUAD_YAW, QUAD_PITCH),
        pose((cx, 140.0, 0.0), 850.0, FRONT, 0.08),
        pose((cx, 140.0, 0.0), 900.0, FRONT, 0.10),
        pose((cx, 140.0, 0.0), 900.0, FRONT, 0.10),
        C.WHOLE,
    ])
    save("gaa")


def zoom_a():
    """a, the process flow: superlattice; dummy gate, inner spacer and epi; release and the gate."""
    name = "gaa_zoom_a"
    m, root = scene_g(name, 3)
    cut_mode("quadl", x=0.0, z=0.0)
    stages = [
        ("sub", "sti", "mesa", "stack"),
        ("sub", "sti", "mesa", "sheets", "sige", "dummy", "spacer", "epi"),
        ("sub", "sti", "mesa", "sheets", "spacer", "epi", "gate", "contact"),
    ]
    for i, parts in enumerate(stages):
        b = empty(f"b{i}", root)
        gaa(b, m, f"st{i}", parts=parts, **ONE)
        show(b, beat(i))
    label("Si sheet", (-200.0, sheet_y(2)[0] + TS / 2, 0.0), root, beat(0))
    label("SiGe spacer layer", (-200.0, GY, 0.0), root, beat(0))
    label("dummy poly gate", (0.0, GTOP, W / 2 + 100), root, beat(1))
    label("inner spacer", (-(GL / 2 + SP / 2), GY, 0.0), root, beat(1))
    label("S/D epi", (-CT_X, Y_TOP, 0.0), root, beat(1))
    label("SiGe out, metal in", (-GL / 4, GY, 0.0), root, beat(2))
    label("gate on 4 sides", (0.0, sheet_y(2)[1], W / 4), root, beat(2))
    t = (0.0, 150.0, 0.0)
    glide_camera(root, [pose(t, 2700.0, QUAD_YAW, QUAD_PITCH)] * 3)
    save(name)


def zoom_b():
    release_scene("gaa_zoom_b")


def zoom_c():
    width_scene("gaa_zoom_c")


def zoom_d():
    power_scene("gaa_zoom_d")


def zoom_e():
    """e, roadmap: a FinFET fin, the nanosheet stack, the forksheet wall, the CFET stack."""
    name = "gaa_zoom_e"
    m, root = scene_g(name, 4)
    cut_mode("x", x=0.0)
    parts = ("sub", "sti", "mesa", "sheets", "spacer", "gate")
    bs = [turned(root, f"b{i}") for i in range(4)]
    D.finfet(bs[0], m, "fin", n=1, parts=("sub", "sti", "fins", "gate", "spacer"), **ONE)
    gaa(bs[1], m, "ns", parts=parts, **ONE)
    gaa(bs[2], m, "fork", parts=parts, lanes=[(-340.0, -40.0, False), (40.0, 340.0, True)], wall=40.0, **ONE)
    gaa(bs[3], m, "cfet", parts=parts, cfet=True, **ONE)
    label("FinFET: gate on 3 sides", (0.0, D.FH, 0.0), bs[0], beat(0))
    label("no gate under the fin", (0.0, -150.0, 0.0), bs[0], beat(0))
    label("nanosheet: gate on 4 sides", (0.0, sheet_y(2)[0] + TS / 2, 0.0), bs[1], beat(1))
    label("forksheet: wall between n and p", (0.0, GTOP - 60, 0.0), bs[2], beat(2))
    label("CFET: nFET over pFET", (0.0, sheet_y(4, True)[0] + TS / 2, 0.0), bs[3], beat(3))
    label("pFET stack below", (0.0, sheet_y(1, True)[0] + TS / 2, 0.0), bs[3], beat(3))
    for i, b in enumerate(bs):
        turn(b)
        show(b, beat(i))
    glide_camera(root, [
        pose((0.0, 280.0, 0.0), 2800.0, FRONT, 0.10),
        pose((0.0, 200.0, 0.0), 2400.0, FRONT, 0.10),
        pose((0.0, 200.0, 0.0), 2600.0, FRONT, 0.10),
        pose((0.0, 460.0, 0.0), 3900.0, FRONT, 0.10),
    ])
    save(name)


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}
