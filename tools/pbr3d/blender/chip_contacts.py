"""CHIP scenes for the CONTACTS node: the overview, zoom-ins a-e and sections 1-10, all on the same
whole-chip cross-section (chip_kit.py), zoomed in on the contact layer.

Run from the repo root, one scene per run (heavy.sh keeps Blender jobs to three at a time):

    blender -b --factory-startup --python tools/pbr3d/blender/chip_contacts.py -- zoom_a
    blender -b --factory-startup --python tools/pbr3d/blender/chip_contacts.py -- sec4
    blender -b --factory-startup --python tools/pbr3d/blender/chip_contacts.py          (the overview)

Each run writes blender/chip_contacts_<scene>.blend and assets/chip_contacts_<scene>.glb (the
overview: chip_contacts.glb). One beat is 8 s.

Overview beats:
  0 whole     the whole chip, the contact layer lit over the two transistors
  1 plugs     in on the plugs: three per transistor (source, gate, drain) up to the thin metal M1
  2 silicide  in on the NMOS: the silicide caps the source and drain under their plugs
  3 squeeze   current runs down the drain plug, a narrow column, from M1 into the silicide
  4 lower R   the silicide lights as current crosses it: the barrier is lower, so is the contact R
  5 whole     back out to the whole chip

Zoom-ins (3 beats each): a silicide to M1, b contact types, c SAC cap and COAG, d contact resistance,
e new metals. Sections (3 to 4 beats each): 1 what happens ... 10 sources, built as detailed
cut-aways of one transistor's contacts by chip_contacts_detail.py (sec_1 .. sec_10 below).

The silicide caps and the liner-and-tungsten plugs are built here (chip_kit's contacts are plain
plugs); the rest of the chip is chip_kit's, unchanged.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_zooms import finish, start  # noqa: E402
import chip_kit as C  # noqa: E402
from chip_kit import F, box, empty, label, mat, route, stream_of, tube  # noqa: E402
import chip_contacts_detail as D  # noqa: E402
import chip_thin_metal_detail as T  # noqa: E402

BEATS = 6
PLUG_TOP = 404.0  # up inside the thin M1 wire (its centre is at level_y("thin", 0) = 410)
SIL = (6.0, 30.0)  # the silicide cap sits on the top of the source and drain blocks
PLUG_R, CORE_R = 28.0, 22.0  # the plug is the liner (outer ring) around a tungsten core
SRC_X, DRN_X = C.NMOS_X - C.SD, C.NMOS_X + C.SD  # the NMOS source is outside, the drain is inside

WHOLE = C.WHOLE


def extra_mats(m):
    m["k_liner"] = mat("chip_contacts_liner", (0.72, 0.60, 0.50), metal=0.6, rough=0.4, alpha=0.5)
    # the tungsten core is see-through, so the current dots inside the plug can be seen
    m["k_wcore"] = mat("chip_contacts_w_core", (0.55, 0.57, 0.62), metal=0.9, rough=0.3, alpha=0.4)
    m["k_sil"] = mat("chip_contacts_silicide", (0.82, 0.86, 0.92), metal=0.9, rough=0.2)
    m["k_sil_on"] = mat("chip_contacts_silicide_on", (0.55, 0.95, 1.0), emit=(0.45, 0.92, 1.0), strength=3.0)
    m["k_lit"] = mat("chip_contacts_lit", (0.45, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=1.0, alpha=0.22)
    m["k_cap"] = mat("chip_contacts_sin_cap", (0.72, 0.80, 0.95), metal=0.1, rough=0.35)


def plug(parent, name, x, y0, m):
    """A tungsten plug from y0 up to the thin metal: a liner ring around a tungsten core."""
    tube(name + "_liner", (x, y0, -60.0), (x, PLUG_TOP, -60.0), PLUG_R, m["k_liner"], parent, verts=12)
    tube(name + "_w", (x, y0, -60.0), (x, PLUG_TOP, -60.0), CORE_R, m["k_wcore"], parent, verts=12)


def contacts(root, m):
    """Per transistor: silicide caps on source and drain, a plug on each, and a plug on the gate."""
    g = empty("contacts", root)
    for cx in (C.NMOS_X, C.PMOS_X):
        for x, tag in ((cx - C.SD, "src"), (cx + C.SD, "drn")):
            box(f"silicide_{tag}{cx:.0f}", (x - 64, SIL[0], -100), (x + 64, SIL[1], -20), m["k_sil"], g)
            plug(g, f"plug_{tag}{cx:.0f}", x, SIL[1], m)
        plug(g, f"plug_gate{cx:.0f}", cx, 120.0, m)
    return g


def sec_start(name, beats):
    m, root = start(name, beats, page="chip")
    D.materials(m)
    return m, root


def whole(**kw):
    a = dict(yaw=0.42, pitch=0.20, fill=0.90, dx=-120.0)
    a.update(kw)
    return D.frame(D.LO, D.HI, **a)


def box_pose(x0, y0, x1, y1, z0=-200.0, **kw):
    a = dict(yaw=0.30, pitch=0.14, fill=0.92, dx=120.0)
    a.update(kw)
    return D.frame((x0, y0, z0), (x1, y1, 0.0), **a)


def path_dots(root, m, name, pts, beat, u0=0.0, u1=0.7, n=10, life=90, size=22.0):
    T.dots(root, m["e"], name, pts, beat, u0, u1, n=n, life=life, size=size)


def sec_1():
    """What happens: the bare transistor in oxide; the contact module on one hole (etch, silicide,
    liner, tungsten); then CMP, via0 and M1 on top."""
    m, root = sec_start("contacts_sec1", 3)
    end = D.F(3, 0) + 100000
    pins = D.device(m, root, shown={
        "ild_full": [(0, D.F(1, 0.02))],
        "sil": [(D.F(1, 0.25), end)],
        "liner": [(D.F(1, 0.5), end)],
        "core": [(D.F(1, 0.75), end)],
        "gc": [(D.F(1, 0.75), end)],
        "beol": D.span(2, 3),
    })
    D.tags(root, [
        (D.span(0, 1), "n+ source/drain epi", pins["epi"]),
        (D.span(0, 1), "metal gate, SiN cap", pins["cap"]),
        (D.span(0, 1), "oxide over the transistor", (D_DRN, 400.0, 2.0)),
        (D.sub(1, 0.02, 0.25), "1 hole etched, oxide cleaned", (D_DRN, 400.0, 0.0)),
        (D.sub(1, 0.25, 0.5), "2 TiSi silicide forms", pins["sil"]),
        (D.sub(1, 0.5, 0.75), "3 Ti/TiN liner", pins["liner"]),
        (D.sub(1, 0.75, 1.0), "4 tungsten fill (WF6 + H2)", pins["core"]),
        (D.span(2, 3), "CMP flat, then via0", pins["v0"]),
        (D.span(2, 3), "M1, the first wiring", pins["m1"]),
        (D.span(2, 3), "W plug", pins["core"]),
    ])
    D.glide(root, [
        box_pose(-1000.0, -500.0, 1000.0, 700.0, z0=-400.0, yaw=0.38, pitch=0.18),
        box_pose(-40.0, -240.0, 640.0, 700.0, yaw=0.25, pitch=0.12),
        whole(),
    ])


def sec_2():
    """From M1 down to silicon: M1 and via0, then the plug, cap and spacer, then the silicide on the epi."""
    m, root = sec_start("contacts_sec2", 3)
    pins = D.device(m, root)
    D.tags(root, [
        (D.span(0, 1), "M1 lines, ~30 nm pitch", pins["m1"]),
        (D.span(0, 1), "via0 lands on the plug", pins["v0"]),
        (D.span(0, 1), "SiN etch stop", (D_DRN + 200, 665.0, 2.0)),
        (D.span(1, 2), "W plug in Ti/TiN liner", pins["liner"]),
        (D.span(1, 2), "SiN cap on the gate", pins["cap"]),
        (D.span(1, 2), "spacer", pins["spacer"]),
        (D.span(2, 3), "TiSi silicide, a few nm", pins["sil"]),
        (D.span(2, 3), "n+ epi, >1e20 /cm3", pins["epi"]),
        (D.span(2, 3), "channel under the gate", (D.GX[2], -40.0, 2.0)),
    ])
    D.glide(root, [
        box_pose(-200.0, 560.0, 800.0, 1180.0, yaw=0.32, pitch=0.18),
        box_pose(-60.0, 100.0, 760.0, 720.0, yaw=0.30, pitch=0.12),
        box_pose(60.0, -260.0, 760.0, 300.0, yaw=0.28, pitch=0.12),
    ])


def sec_3():
    """Contact types: the trench bar and the gate plug seen from above; a misaligned contact held
    off by the SiN cap and the gate contact over the channel; then conventional against selective W."""
    m, root = sec_start("contacts_sec3", 3)
    pins = D.device(m, root, shown={"beol": [(0, 0)]})
    mis = D.group("misaligned", root, D.span(1, 2))
    D.box("mis_core", (D_DRN - 10, D.SIL[1] + 30, -400.0), (D_DRN + 190, D.ILD0_TOP + 1, 3.0), m["hl_soft"], mis)
    D.box("cap_hit", (D.GX[2] - D.GL - D.SP, D.CAP_TOP - 40, -400.0), (D.GX[2] - D.GL + 10, D.CAP_TOP, 3.5), m["good"], mis)
    ox = 2200.0
    a = T.grow("selw", (ox + 300.0, 0.0, 0.0), root, D.F(2, 0.1), D.F(2, 0.8))
    g2 = D.group("types", root, D.span(2, 3))
    conv = D.plug(m, g2, "conv", ox - 300.0, 200.0, 30.0, "w", seam=True)
    D.plug(m, g2, "selw_hole", ox + 300.0, 200.0, 0.0, "void", block=True)
    D.box("selw_core", T.rel((ox + 300.0, 0.0, 0.0), (ox + 300.0 - 99, 0.0, -199.0)),
          T.rel((ox + 300.0, 0.0, 0.0), (ox + 300.0 + 99, 603.0, 2.5)), m["w"], a)
    D.tags(root, [
        (D.span(0, 1), "trench contact: a long bar", (D_DRN, D.ILD0_TOP + 2, -500.0)),
        (D.span(0, 1), "gate contact: one plug", (0.0, D.ILD0_TOP + 2, -120.0)),
        (D.span(1, 2), "misaligned contact", (D_DRN + 90, 400.0, 4.0)),
        (D.span(1, 2), "SiN cap/spacer stops it", (D.GX[2] - D.GL - 30, D.CAP_TOP - 20, 4.0)),
        (D.span(1, 2), "gate contact over the channel", pins["gc"]),
        (D.span(2, 3), "CVD W: liner + seam", conv[0]),
        (D.span(2, 3), "selective W: bottom-up", (ox + 300.0, 300.0, 3.0)),
    ])
    D.glide(root, [
        D.frame((-700.0, -100.0, -1200.0), (700.0, 700.0, 0.0), yaw=0.75, pitch=0.62, fill=0.95, dx=120.0),
        box_pose(-200.0, -100.0, 760.0, 720.0, z0=-300.0, yaw=0.30, pitch=0.18),
        D.frame((ox - 480.0, -100.0, -400.0), (ox + 480.0, 620.0, 0.0), yaw=0.22, pitch=0.16, fill=0.92, dx=150.0),
    ])


def sbh_bar(m, root, x, beat):
    """The Schottky barrier as a red bar beside the contact: 0.7 eV, dropping to 0.34 eV mid-beat."""
    g = D.group("sbh", root, D.span(beat, beat + 1))
    p = D.empty("sbh_p", g, D.P(x, 0.0, -60.0))
    T.scale_keys(p, [(0, (1, 1, 1)), (D.F(beat, 0.45), (1, 1, 1)), (D.F(beat, 0.6), (1, 1, 0.34 / 0.7))])
    D.box("sbh_bar", T.rel((x, 0.0, -60.0), (x - 60, 0.0, -120.0)), T.rel((x, 0.0, -60.0), (x + 60, 700.0, 0.0)), m["sbh"], p)
    D.box("sbh_base", (x - 90, -30.0, -150.0), (x + 90, 0.0, 30.0), m["base"], g)
    return g


def sec_4():
    """Why contact resistance is the bottleneck: the series path; the plug narrower than tungsten's
    mean free path; the liner's share of a small hole; the silicide's Schottky barrier."""
    m, root = sec_start("contacts_sec4", 4)
    pins = D.device(m, root)
    s, d = D.SX
    path_dots(root, m, "path", [(d, 1020.0, 8.0), (d, 160.0, 8.0), (d, 40.0, 8.0), (0.0, -40.0, 8.0),
                                 (s, 40.0, 8.0), (s, 1020.0, 8.0)], 0, 0.0, 0.6, n=10, life=150)
    # beat 1: the mean free path against the tungsten core
    core_w = 2 * (D.TS_HALF - D.LINER)
    mf = D.group("mfp", root, D.span(1, 2))
    D.box("mfp_rod", (d - 95.5, 455.0, 4.0), (d + 95.5, 470.0, 8.0), m["mfp"], mf)
    zig = [(d - 50 + (100 if k % 2 else 0), 620.0 - 60.0 * k, 9.0) for k in range(8)]
    path_dots(root, m, "bounce", zig, 1, 0.0, 0.7, n=6, life=110, size=16.0)
    # beat 2: the liner's share in a big hole and a small one
    ox = 2000.0
    lg = D.group("squeeze", root, D.span(2, 3))
    big = D.plug(m, lg, "big", ox, 400.0, 30.0, "w", y1=500.0)
    small = D.plug(m, lg, "small", ox + 600.0, 150.0, 30.0, "w", y1=500.0)
    # beat 3: the barrier
    sbh_bar(m, root, 1250.0, 3)
    path_dots(root, m, "few", [(d, 400.0, 8.0), (d, 150.0, 8.0), (d, -60.0, 8.0)], 3, 0.0, 0.4, n=3, life=70)
    path_dots(root, m, "many", [(d, 400.0, 8.0), (d, 150.0, 8.0), (d, -60.0, 8.0)], 3, 0.6, 0.95, n=9, life=40)
    D.tags(root, [
        (D.span(0, 1), "R wire + via", pins["m1"]),
        (D.span(0, 1), "R plug", pins["core"]),
        (D.span(0, 1), "R contact: silicide to Si", (D.SX[0] + 70, 125.0, 4.0)),
        (D.span(0, 1), "R channel", (60.0, -80.0, 2.0)),
        (D.span(1, 2), "W core ~14 nm wide", (d, 560.0, 4.0)),
        (D.span(1, 2), "W mean free path 19.1 nm", (d + 95.0, 462.0, 8.0)),
        (D.span(2, 3), "40 nm hole: ~72% W", big[0]),
        (D.span(2, 3), "15 nm hole: ~36% W", small[0]),
        (D.sub(3, 0.0, 0.5), "Schottky barrier ~0.7 eV", (1250.0, 690.0, 2.0)),
        (D.sub(3, 0.5, 1.0), "~0.34 eV, dopant segregation", (1250.0, 330.0, 2.0)),
        (D.span(3, 4), "silicide / epi interface", pins["sil"]),
    ])
    D.glide(root, [
        whole(),
        box_pose(d - 260, 300.0, d + 260, 700.0, yaw=0.12, pitch=0.06, dx=100.0),
        D.frame((ox - 330.0, -100.0, -500.0), (ox + 730.0, 520.0, 0.0), yaw=0.18, pitch=0.62, fill=0.92, dx=140.0),
        box_pose(d - 200, -250.0, 1360.0, 720.0, yaw=0.20, pitch=0.10),
    ])
    assert core_w == 140.0


def sec_5():
    """By the numbers: W's mean free path against the core; Schottky barriers; bulk resistivities;
    the vendor and fab claims pinned to their parts."""
    m, root = sec_start("contacts_sec5", 4)
    pins = D.device(m, root)
    d = D_DRN
    mf = D.group("mfp", root, D.span(0, 1))
    D.box("mfp_rod", (d - 95.5, 455.0, 4.0), (d + 95.5, 470.0, 8.0), m["mfp"], mf)
    zig = [(d - 50 + (100 if k % 2 else 0), 620.0 - 60.0 * k, 9.0) for k in range(8)]
    path_dots(root, m, "bounce", zig, 0, 0.0, 0.7, n=6, life=110, size=16.0)
    ox = 2200.0
    bg = D.group("sbh_bars", root, D.span(1, 2))
    p1, _ = D.column(m, bg, "nisi", ox, 0.68, 800.0, m["sbh"])
    p2, _ = D.column(m, bg, "tisi", ox + 300, 0.58, 800.0, m["sbh"])
    p3, _ = D.column(m, bg, "seg", ox + 600, 0.34, 800.0, m["sbh"])
    rx = 4200.0
    rg = D.group("rho_bars", root, D.span(2, 3))
    rho = [("Cu 1.7", 1.7, "cu"), ("Mo 5.3", 5.3, "mo"), ("W 5.6", 5.6, "w"), ("Co 6.2", 6.2, "co"), ("Ru 7.1", 7.1, "ru")]
    rp = []
    for k, (nm, v, mk) in enumerate(rho):
        pt, _ = D.column(m, rg, f"rho{k}", rx + 260 * k, v, 80.0, m[mk], w=150.0)
        rp.append((nm, pt))
    D.tags(root, [
        (D.span(0, 1), "W mean free path 19.1 nm", (d + 95.0, 462.0, 8.0)),
        (D.span(0, 1), "core ~14 nm", (d, 560.0, 4.0)),
        (D.span(1, 2), "NiSi 0.65-0.7 eV", p1),
        (D.span(1, 2), "TiSi2 0.58 eV", p2),
        (D.span(1, 2), "segregated 0.34 eV", p3),
    ] + [(D.span(2, 3), nm + " uOhm-cm", pt) for nm, pt in rp] + [
        (D.span(3, 4), "Applied Volta W: up to 90% lower R", pins["core"]),
        (D.span(3, 4), "TSMC N2: MOL R+C up to 20% lower", pins["gc"]),
        (D.span(3, 4), "Intel 10 nm: cobalt M0/M1", pins["m1"]),
    ])
    D.glide(root, [
        box_pose(d - 260, 300.0, d + 260, 700.0, yaw=0.12, pitch=0.06, dx=100.0),
        D.frame((ox - 120.0, -40.0, -200.0), (ox + 720.0, 560.0, 0.0), yaw=0.22, pitch=0.12, fill=0.9, dx=160.0),
        D.frame((rx - 120.0, -40.0, -200.0), (rx + 1160.0, 580.0, 0.0), yaw=0.22, pitch=0.12, fill=0.9, dx=160.0),
        whole(),
    ])


def sec_6():
    """Applied Materials: FY2025 revenue as a stacked bar, the Semiconductor Systems split, then the
    contact steps its tools run, pinned on the device."""
    m, root = sec_start("contacts_sec6", 3)
    pins = D.device(m, root)
    ox, s = 2600.0, 50.0  # 50 scene mm per $1B
    g1 = D.group("rev", root, D.span(0, 3))
    segs = [("Semi Systems $20.80B", 20.80, "amat1"), ("Services ~$6.5B", 6.53, "amat2"), ("other ~$1.0B", 1.04, "amat3")]
    y, p_rev = 0.0, []
    for k, (nm, v, mk) in enumerate(segs):
        D.box(f"rev{k}", (ox - 120, y, -240.0), (ox + 120, y + v * s, 0.0), m[mk], g1)
        p_rev.append((nm, (ox + 120, y + v * s / 2, 2.0)))
        y += v * s
    D.box("rev_base", (ox - 150, -30.0, -270.0), (ox + 150, 0.0, 30.0), m["base"], g1)
    g2 = D.group("semi", root, D.span(1, 3))
    split = [("foundry/logic 67%", 0.67, "amat1"), ("DRAM 26%", 0.26, "amat2"), ("NAND 7%", 0.07, "amat3")]
    y, p_semi = 0.0, []
    for k, (nm, f, mk) in enumerate(split):
        h = f * 20.80 * s
        D.box(f"semi{k}", (ox + 500, y, -240.0), (ox + 740, y + h, 0.0), m[mk], g2)
        p_semi.append((nm, (ox + 740, y + h / 2, 2.0)))
        y += h
    D.box("semi_base", (ox + 470, -30.0, -270.0), (ox + 770, 0.0, 30.0), m["base"], g2)
    D.tags(root, [(D.span(0, 1), "FY2025 $28.37B: " + p_rev[0][0], p_rev[0][1])]
           + [(D.span(0, 1), nm, pt) for nm, pt in p_rev[1:]]
           + [(D.span(1, 2), nm, pt) for nm, pt in p_semi]
           + [(D.span(2, 3), "Endura PVD: Ti/TiN liner", pins["liner"]),
              (D.span(2, 3), "CVD/ALD: tungsten fill", pins["core"]),
              (D.span(2, 3), "selective W, cobalt", pins["gc"])])
    D.glide(root, [
        D.frame((ox - 160.0, -40.0, -260.0), (ox + 160.0, 1420.0, 0.0), yaw=0.22, pitch=0.10, fill=0.82, dx=260.0),
        D.frame((ox - 160.0, -40.0, -260.0), (ox + 780.0, 1420.0, 0.0), yaw=0.22, pitch=0.10, fill=0.9, dx=220.0),
        whole(),
    ])


def sec_7():
    """New metals: a tungsten plug with its TiN liner and seam, a cobalt plug with a thinner liner,
    and a barrierless molybdenum plug, side by side, one added per beat."""
    m, root = sec_start("contacts_sec7", 3)
    xs = (0.0, 500.0, 1000.0)
    w = D.plug(m, root, "w", xs[0], 200.0, 30.0, "w", seam=True)
    cg = D.group("co_g", root, D.span(1, 3))
    co = D.plug(m, cg, "co", xs[1], 200.0, 15.0, "co", lm="tin")
    mg = D.group("mo_g", root, D.span(2, 3))
    mo = D.plug(m, mg, "mo", xs[2], 200.0, 0.0, "mo")
    for k, x in enumerate(xs[1:], 1):  # empty holes until the plug arrives
        hole = D.group(f"hole{k}", root, [(0, D.F(k, 0))])
        D.plug(m, hole, f"hole{k}", x, 200.0, 0.0, "void")
    D.tags(root, [
        (D.span(0, 3), "W: TiN ~3 nm a side", w[1]),
        (D.span(0, 1), "seam down the middle", (xs[0], 300.0, 4.0)),
        (D.span(1, 3), "Co: thinner liner (Intel 10 nm)", co[0]),
        (D.span(2, 3), "Mo: no barrier, all metal", mo[0]),
    ])
    pose = D.frame((-260.0, -100.0, -300.0), (1260.0, 620.0, 0.0), yaw=0.22, pitch=0.16, fill=0.94, dx=170.0)
    D.glide(root, [pose, pose, pose])


def sec_8():
    """Who makes it: the tool makers pinned to the liner and fill, the fabs to the contact scheme,
    then the buyers and the EDA tools that extract contact RC along the current path."""
    m, root = sec_start("contacts_sec8", 3)
    pins = D.device(m, root)
    s, d = D.SX
    path_dots(root, m, "rc", [(d, 1020.0, 8.0), (d, 160.0, 8.0), (d, 40.0, 8.0), (0.0, -40.0, 8.0),
                               (s, 40.0, 8.0), (s, 1020.0, 8.0)], 2, 0.0, 0.6, n=10, life=150)
    D.tags(root, [
        (D.span(0, 1), "Applied: liner, Co, selective W", pins["liner"]),
        (D.span(0, 1), "Lam ALTUS: W and Mo fill", pins["core"]),
        (D.span(1, 2), "TSMC, Intel design the scheme", pins["sil"]),
        (D.span(1, 2), "Intel first: COAG at 10 nm", pins["gc"]),
        (D.span(2, 3), "Synopsys, Cadence: contact RC", pins["core"]),
        (D.span(2, 3), "Samsung, SK hynix, Micron buy", pins["m1"]),
        (D.span(2, 3), "TEL: CVD and ALD", pins["liner"]),
    ])
    D.glide(root, [
        box_pose(-60.0, -100.0, 760.0, 760.0, yaw=0.30, pitch=0.14),
        box_pose(-300.0, -100.0, 760.0, 760.0, yaw=0.30, pitch=0.14),
        whole(),
    ])


def sec_9():
    """Chokepoints: molybdenum contacts need new tools; a barrierless plug's adhesion voids and
    diffusion; and the contact area shrinking by four for half the width."""
    m, root = sec_start("contacts_sec9", 3)
    pins = D.device(m, root, metal="mo", liner=0.0)
    d = D_DRN
    bad = D.group("barrierless", root, D.span(1, 2))
    D.box("void1", (d - 100, 300.0, -300.0), (d - 88, 420.0, 4.0), m["void"], bad)
    for k, (dx, y) in enumerate(((-140, 520), (-125, 330), (130, 450), (145, 260))):
        D.ball(f"diff{k}", (d + dx, y, 6.0), 14.0, m["bad"], bad, 10)
    ox = 2200.0
    g = D.group("area", root, D.span(2, 3))
    big = D.plug(m, g, "a20", ox, 200.0, 0.0, "w", y1=400.0)
    small = D.plug(m, g, "a10", ox + 500, 100.0, 0.0, "w", y1=400.0)
    rb1, _ = D.column(m, g, "r20", ox + 1000, 1.0, 120.0, m["rbar"], w=120.0)
    rb2, _ = D.column(m, g, "r10", ox + 1250, 4.0, 120.0, m["rbar"], w=120.0)
    D.tags(root, [
        (D.span(0, 1), "Mo plugs: new tools, new qualification", pins["core"]),
        (D.span(0, 1), "no liner", pins["ild"]),
        (D.span(1, 2), "void: poor adhesion", (d - 94, 360.0, 5.0)),
        (D.span(1, 2), "metal diffusing into oxide", (d + 130, 450.0, 7.0)),
        (D.span(2, 3), "20 nm contact", big[0]),
        (D.span(2, 3), "10 nm: 1/4 the area", small[0]),
        (D.span(2, 3), "R = rho-c / A: ~4x", rb2),
        (D.span(2, 3), "R at 20 nm", rb1),
    ])
    D.glide(root, [
        box_pose(-60.0, -100.0, 760.0, 760.0, yaw=0.30, pitch=0.14),
        box_pose(d - 260, 150.0, d + 260, 650.0, yaw=0.14, pitch=0.06, dx=110.0),
        D.frame((ox - 250.0, -130.0, -300.0), (ox + 1330.0, 520.0, 0.0), yaw=0.20, pitch=0.30, fill=0.92, dx=140.0),
    ])


def sec_10():
    """Sources: the device, turning slowly. The sources are the beat text."""
    m, root = sec_start("contacts_sec10", 3)
    pins = D.device(m, root)
    D.tags(root, [(D.span(0, 3), "contacts: silicide, liner, W", pins["core"])])
    D.glide(root, [whole(yaw=0.25), whole(yaw=0.42), whole(yaw=0.60)])


SECTIONS = {f"sec{n}": f for n, f in enumerate(
    (sec_1, sec_2, sec_3, sec_4, sec_5, sec_6, sec_7, sec_8, sec_9, sec_10), 1)}


# ---- the overview and zoom-ins a-e: detailed cut-aways --------------------------------------
# The overview opens on the whole chip (chip_kit, with this page's lined plugs), then swaps it for
# the detailed transistor (chip_contacts_detail.device), scaled to sit where the NMOS is, and
# glides in. Current rides the real path as beads. The zoom-ins are full-size cut-aways.

INSET_O = (C.NMOS_X, 0.0, 0.0)  # the device's silicon top on the chip's
INSET_S = 0.2


def ipose(pose):
    return T.world(pose, INSET_O, INSET_S)


def build_overview():
    m, root = start("contacts", BEATS, page="chip")
    C.mats(m)
    extra_mats(m)
    D.materials(m)
    whole_iv = [(0, F(1, 0)), (F(5, 0), F(6, 0) + 1000)]
    g = D.group("chip_whole", root, whole_iv)
    C.silicon(g, m)
    C.transistor(g, m, C.NMOS_X, True)
    C.transistor(g, m, C.PMOS_X, False)
    contacts(g, m)
    C.wiring(g, m)
    C.bumps(g, m)
    for cx in (C.NMOS_X, C.PMOS_X):
        C.overlay(g, f"lit_contacts{cx:.0f}", (cx - C.SD - 80, -10, -110), (cx + C.SD + 80, PLUG_TOP + 8, -10), m["k_lit"], whole_iv)
    label("contacts", (1150.0, 230.0, 0), root, whole_iv)
    s = T.inset(root, INSET_O, INSET_S, D.span(1, 5))
    pins = D.device(m, s)
    sx, dx = D.SX
    squeeze = [(dx, 1100.0, 10.0), (dx, 880.0, 10.0), (dx, 660.0, 10.0), (dx, 150.0, 10.0), (dx, -120.0, 10.0)]
    path_dots(s, m, "squeeze", squeeze, 3, 0.0, 0.75, n=12, life=80, size=20.0)
    for k, x in enumerate(D.SX):
        T.front_glow(f"sil_glow{k}", (x - 110, D.SIL[0] - 4), (x + 110, D.SIL[1] + 4), m["hl_soft"], s, D.span(4, 5), z=5.0)
    path_dots(s, m, "cross", [(dx, 500.0, 10.0), (dx, 150.0, 10.0), (dx, -150.0, 10.0)], 4, 0.0, 0.85, n=14, life=45, size=18.0)
    D.tags(s, [
        (D.span(1, 2), "source plug", (sx, 380.0, 4.0)),
        (D.span(1, 2), "gate plug", pins["gc"]),
        (D.span(1, 2), "drain plug", pins["core"]),
        (D.span(1, 2), "M1, the first metal", pins["m1"]),
        (D.span(2, 3), "TiSi silicide", pins["sil"]),
        (D.span(2, 3), "n+ drain epi", pins["epi"]),
        (D.span(2, 3), "W plug, Ti/TiN liner", pins["liner"]),
        (D.span(3, 4), "current from M1 and via0", (dx, 1000.0, 10.0)),
        (D.span(3, 4), "squeezed into a ~15-20 nm plug", (dx, 400.0, 10.0)),
        (D.span(4, 5), "silicide: lower barrier to Si", pins["sil"]),
        (D.span(4, 5), "contact R ~ rho-c / area", (dx, -100.0, 10.0)),
    ])
    D.glide(root, [
        C.WHOLE,
        ipose(whole()),
        ipose(box_pose(60.0, -260.0, 760.0, 420.0, yaw=0.28, pitch=0.12)),
        ipose(box_pose(dx - 300, -200.0, dx + 300, 1180.0, yaw=0.25, pitch=0.12)),
        ipose(box_pose(-460.0, -260.0, 760.0, 560.0, yaw=0.25, pitch=0.10)),
        C.WHOLE,
    ])


def zoom_start(name):
    m, root = start(name, 3, page="chip")
    D.materials(m)
    return m, root


CLOSE = dict(x0=-40.0, y0=-240.0, x1=640.0, y1=700.0)


def zoom_a():
    """The contact module on the drain: clean and silicide, liner and tungsten, CMP, via0 and M1."""
    m, root = zoom_start("contacts_zoom_a")
    end = F(3, 0) + 100000
    pins = D.device(m, root, shown={
        "ild_full": [(0, F(0, 0.2))], "sil": [(F(0, 0.45), end)], "liner": [(F(1, 0.1), end)],
        "core": [(F(1, 0.6), end)], "gc": [(F(1, 0.6), end)], "beol": [(F(2, 0.25), end)]})
    d = D.SX[1]
    nat = D.group("native", root, [(0, F(0, 0.3))])
    for k, x in enumerate(D.SX):
        D.box(f"native{k}", (x - 110, D.SIL[0], -1200.0), (x + 110, D.SIL[0] + 14, 2.5), m["air"], nat)
    for k, x in enumerate(D.SX):
        T.front_glow(f"silg{k}", (x - 110, D.SIL[0] - 4), (x + 110, D.SIL[1] + 4), m["hl_soft"], root, [(F(0, 0.45), F(1, 0))], z=5.0)
    path_dots(root, m, "wf6", [(d, 1100.0, -300.0), (d, 200.0, -300.0)], 1, 0.12, 0.6, n=8, life=40, size=16.0)
    path_dots(root, m, "sig", [(d, -100.0, 10.0), (d, 150.0, 10.0), (d, 660.0, 10.0), (d, 900.0, 10.0), (d, 1100.0, 10.0)],
              2, 0.35, 0.9, n=8, life=70, size=20.0)
    D.tags(root, [
        (D.sub(0, 0.0, 0.3), "native oxide on the epi", (d - 40, D.SIL[0] + 7, 4.0)),
        (D.sub(0, 0.15, 0.45), "hole etched through the oxide", (d, 400.0, -200.0)),
        (D.sub(0, 0.45, 1.0), "Ti + Si -> TiSi silicide", pins["sil"]),
        (D.sub(1, 0.1, 1.0), "Ti/TiN liner", pins["liner"]),
        (D.sub(1, 0.15, 0.6), "WF6 + H2 deposit tungsten", (d, 700.0, -300.0)),
        (D.sub(1, 0.6, 1.0), "W fill", pins["core"]),
        (D.sub(2, 0.0, 0.25), "CMP: plugs polished flat", (d + 250, 652.0, -300.0)),
        (D.sub(2, 0.25, 1.0), "SiN etch stop", (d + 250, 665.0, 2.0)),
        (D.sub(2, 0.25, 1.0), "via0 lands on the plug", pins["v0"]),
        (D.sub(2, 0.25, 1.0), "M1", pins["m1"]),
    ])
    close = box_pose(**CLOSE, yaw=0.25, pitch=0.14)
    D.glide(root, [close, close, whole()])


def zoom_b():
    """Contact types: the trench bar along the source and drain, the gate plug, then conventional
    CVD tungsten against selective, bottom-up tungsten."""
    m, root = zoom_start("contacts_zoom_b")
    pins = D.device(m, root, shown={"beol": [(F(1, 0), F(3, 0) + 1000)]})
    for k, x in enumerate(D.SX):
        path_dots(root, m, f"bar{k}", [(x, D.ILD0_TOP + 20, -60.0), (x, D.ILD0_TOP + 20, -1150.0)], 0, 0.0, 0.7, n=6, life=90, size=22.0)
    path_dots(root, m, "gate", [(0.0, 1020.0, 10.0), (0.0, 880.0, 10.0), (0.0, 600.0, 10.0), (0.0, 250.0, 10.0)], 1, 0.0, 0.7, n=8, life=70, size=20.0)
    ox = 2200.0
    a = T.grow("selw", (ox + 300.0, 0.0, 0.0), root, F(2, 0.1), F(2, 0.8))
    g2 = D.group("types", root, D.span(2, 3))
    conv = D.plug(m, g2, "conv", ox - 300.0, 200.0, 30.0, "w", seam=True)
    D.plug(m, g2, "selw_hole", ox + 300.0, 200.0, 0.0, "void")
    D.box("selw_core", T.rel((ox + 300.0, 0.0, 0.0), (ox + 300.0 - 99, 0.0, -199.0)),
          T.rel((ox + 300.0, 0.0, 0.0), (ox + 300.0 + 99, 603.0, 2.5)), m["w"], a)
    path_dots(root, m, "wf6", [(ox + 300.0, 1000.0, -100.0), (ox + 300.0, 60.0, -100.0)], 2, 0.05, 0.7, n=8, life=40, size=16.0)
    D.tags(root, [
        (D.span(0, 1), "trench contact: one long bar", (D.SX[1], D.ILD0_TOP + 2, -500.0)),
        (D.span(0, 1), "straps the whole drain", (D.SX[1], D.ILD0_TOP + 2, -1000.0)),
        (D.span(1, 2), "gate contact: a plug", pins["gc"]),
        (D.span(1, 2), "through the SiN cap", (60.0, 520.0, 3.0)),
        (D.span(2, 3), "CVD W: liner + seam", conv[0]),
        (D.span(2, 3), "selective W grows bottom-up", (ox + 300.0, 300.0, 3.0)),
    ])
    D.glide(root, [
        D.frame((-700.0, -100.0, -1200.0), (700.0, 700.0, 0.0), yaw=0.75, pitch=0.62, fill=0.95, dx=120.0),
        box_pose(-360.0, 100.0, 360.0, 1180.0, yaw=0.28, pitch=0.14),
        D.frame((ox - 480.0, -100.0, -400.0), (ox + 480.0, 1000.0, 0.0), yaw=0.22, pitch=0.16, fill=0.92, dx=150.0),
    ])


def zoom_c():
    """SAC cap and COAG: a misaligned contact stopped by the SiN cap, the gate contact over the
    channel, then two standard cells from above: the COAG one shorter."""
    m, root = zoom_start("contacts_zoom_c")
    pins = D.device(m, root, shown={"beol": [(0, 0)]})
    d = D.SX[1]
    mis = D.group("misaligned", root, D.span(0, 1))
    D.box("mis_core", (d - 10, D.SIL[1] + 30, -400.0), (d + 190, D.ILD0_TOP + 1, 3.0), m["hl_soft"], mis)
    D.box("cap_hit", (D.GX[2] - D.GL - D.SP, D.CAP_TOP - 40, -400.0), (D.GX[2] - D.GL + 10, D.CAP_TOP, 3.5), m["good"], mis)
    T.front_glow("chan", (-80.0, -70.0), (80.0, -5.0), m["sig_soft"], root, D.span(1, 2), z=4.0)
    path_dots(root, m, "gate", [(0.0, 700.0, 10.0), (0.0, 600.0, 10.0), (0.0, 250.0, 10.0)], 1, 0.0, 0.7, n=7, life=60, size=20.0)
    ox1, ox2 = 4000.0, 6000.0
    c1 = D.group("cell_tall", root, D.span(2, 3))
    _, p1, _ = T.cell(m, c1, ox=ox1)
    D.box("gc_side", (ox1 - 245, T.M1_Y[1], -800.0), (ox1 - 155, T.M1_Y[1] + 30, -740.0), m["hl"], c1)
    c2 = D.group("cell_short", root, D.span(2, 3))
    sq = D.empty("cell_sq", c2)
    sq.scale = (1.0, 0.9, 1.0)  # Blender Y is scene -z: the cell is 10% shorter
    _, p2, _ = T.cell(m, sq, ox=ox2)
    D.box("gc_over", (ox2 - 245, T.M1_Y[1], -450.0), (ox2 - 155, T.M1_Y[1] + 30, -390.0), m["hl"], sq)
    D.tags(root, [
        (D.span(0, 1), "SiN cap on the gate", pins["cap"]),
        (D.span(0, 1), "misaligned contact stops on SiN", (D.GX[2] - D.GL - 30, D.CAP_TOP - 20, 4.0)),
        (D.span(1, 2), "gate contact over the channel", pins["gc"]),
        (D.span(1, 2), "active channel (COAG)", (0.0, -40.0, 5.0)),
        (D.span(2, 3), "gate contact off the active area", (ox1 - 200, T.M1_Y[1] + 30, -770.0)),
        (D.span(2, 3), "COAG: ~10% shorter (Intel)", (ox2 - 200, T.M1_Y[1] + 30, -378.0)),
    ])
    D.glide(root, [
        box_pose(-200.0, -100.0, 760.0, 720.0, z0=-300.0, yaw=0.30, pitch=0.18),
        box_pose(-460.0, -150.0, 460.0, 760.0, yaw=0.25, pitch=0.12),
        D.frame((ox1 - 980.0, -60.0, -960.0), (ox2 + 980.0, 220.0, 120.0), yaw=0.05, pitch=1.15, fill=0.95, dx=-120.0),
    ])


def zoom_d():
    """Contact resistance: area (rho_c / A), the liner squeeze, then the Schottky barrier lowered."""
    m, root = zoom_start("contacts_zoom_d")
    D.device(m, root)
    ox = 2200.0
    g = D.group("area", root, D.span(0, 1))
    big = D.plug(m, g, "a20", ox, 200.0, 0.0, "w", y1=400.0)
    small = D.plug(m, g, "a10", ox + 500, 100.0, 0.0, "w", y1=400.0)
    rb1, _ = D.column(m, g, "r20", ox + 1000, 1.0, 120.0, m["rbar"], w=120.0)
    rb2, _ = D.column(m, g, "r10", ox + 1250, 4.0, 120.0, m["rbar"], w=120.0)
    path_dots(root, m, "big", [(ox, 600.0, 5.0), (ox, 0.0, 5.0)], 0, 0.0, 0.8, n=10, life=40, size=16.0)
    path_dots(root, m, "small", [(ox + 500, 600.0, 5.0), (ox + 500, 0.0, 5.0)], 0, 0.0, 0.8, n=10, life=90, size=16.0)
    ox2 = 5200.0
    lg = D.group("squeeze", root, D.span(1, 2))
    b40 = D.plug(m, lg, "big", ox2, 400.0, 30.0, "w", y1=500.0)
    b15 = D.plug(m, lg, "small", ox2 + 600.0, 150.0, 30.0, "w", y1=500.0)
    sbh_bar(m, root, 1250.0, 2)
    dd = D.SX[1]
    path_dots(root, m, "few", [(dd, 400.0, 8.0), (dd, 150.0, 8.0), (dd, -60.0, 8.0)], 2, 0.0, 0.4, n=3, life=70)
    path_dots(root, m, "many", [(dd, 400.0, 8.0), (dd, 150.0, 8.0), (dd, -60.0, 8.0)], 2, 0.6, 0.95, n=9, life=40)
    D.tags(root, [
        (D.span(0, 1), "20 nm contact", big[0]),
        (D.span(0, 1), "10 nm: 1/4 the area", small[0]),
        (D.span(0, 1), "R = rho-c / A: ~4x", rb2),
        (D.span(1, 2), "40 nm hole: ~72% W", b40[0]),
        (D.span(1, 2), "15 nm hole: ~36% W", b15[0]),
        (D.sub(2, 0.0, 0.5), "Schottky barrier ~0.7 eV", (1250.0, 690.0, 2.0)),
        (D.sub(2, 0.5, 1.0), "~0.34 eV, dopant segregation", (1250.0, 330.0, 2.0)),
        (D.span(2, 3), "silicide / epi interface", (dd + 70, 125.0, 4.0)),
    ])
    D.glide(root, [
        D.frame((ox - 250.0, -130.0, -300.0), (ox + 1330.0, 620.0, 0.0), yaw=0.20, pitch=0.30, fill=0.92, dx=140.0),
        D.frame((ox2 - 330.0, -100.0, -500.0), (ox2 + 730.0, 520.0, 0.0), yaw=0.18, pitch=0.62, fill=0.92, dx=140.0),
        box_pose(dd - 200, -250.0, 1360.0, 720.0, yaw=0.20, pitch=0.10),
    ])


def zoom_e():
    """New metals: tungsten's mean free path against the plug, then a tungsten and a cobalt plug,
    then molybdenum added, barrierless."""
    m, root = zoom_start("contacts_zoom_e")
    D.device(m, root)
    d = D.SX[1]
    mf = D.group("mfp", root, D.span(0, 1))
    D.box("mfp_rod", (d - 95.5, 455.0, 4.0), (d + 95.5, 470.0, 8.0), m["mfp"], mf)
    zig = [(d - 50 + (100 if k % 2 else 0), 620.0 - 60.0 * k, 9.0) for k in range(8)]
    path_dots(root, m, "bounce", zig, 0, 0.0, 0.7, n=6, life=110, size=16.0)
    ox = 3000.0
    xs = (ox, ox + 500.0, ox + 1000.0)
    tg = D.group("trio", root, D.span(1, 3))
    w = D.plug(m, tg, "w", xs[0], 200.0, 30.0, "w", seam=True)
    co = D.plug(m, tg, "co", xs[1], 200.0, 15.0, "co")
    mg = D.group("mo_g", root, D.span(2, 3))
    mo = D.plug(m, mg, "mo", xs[2], 200.0, 0.0, "mo")
    hole = D.group("hole", root, D.span(1, 2))
    D.plug(m, hole, "hole", xs[2], 200.0, 0.0, "void")
    for k, x in enumerate(xs):
        path_dots(root, m, f"i{k}", [(x, 640.0, 5.0), (x, 40.0, 5.0)], 2 if k == 2 else 1, 0.0, 0.8, n=6, life=60, size=16.0)
    D.tags(root, [
        (D.span(0, 1), "W mean free path 19.1 nm", (d + 95.0, 462.0, 8.0)),
        (D.span(0, 1), "W core ~14 nm", (d, 560.0, 4.0)),
        (D.span(1, 3), "W ~5.6 uOhm-cm, thick liner", w[1]),
        (D.span(1, 3), "Co ~6.2: Intel 10 nm (2017)", co[0]),
        (D.span(2, 3), "Mo ~5.3, no barrier", mo[0]),
    ])
    trio = D.frame((ox - 260.0, -100.0, -300.0), (ox + 1260.0, 620.0, 0.0), yaw=0.22, pitch=0.16, fill=0.94, dx=170.0)
    D.glide(root, [box_pose(d - 260, 300.0, d + 260, 700.0, yaw=0.12, pitch=0.06, dx=100.0), trio, trio])


ZOOMS = {"zoom_a": zoom_a, "zoom_b": zoom_b, "zoom_c": zoom_c, "zoom_d": zoom_d, "zoom_e": zoom_e}


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = argv[0] if argv else "overview"
    if name == "overview":
        build_overview()
        finish("contacts", page="chip")
    else:
        {**SECTIONS, **ZOOMS}[name]()
        finish("contacts_" + name, page="chip")
