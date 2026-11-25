"""Zoom-ins (a-e) for the MICROBUMP page, three beats each, each a real scene with its own parts,
beads and cameras (diagrams_nodes/packaging/microbump/zooms.rs):

  a C4, microbump, hybrid bond   the three joints side by side at one scale, cut open
  b making a joint               pillars plated, solder capped, placed and reflowed, underfilled
  c pitch and the solder wall    bumps at shrinking pitch until the solder bridges; hybrid pads
  d stress, warpage, underfill   the package heats, the substrate bows, the corner joints strain
  e current through the bumps    electrons through one joint, a void grows, many bumps share

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_microbump_zooms.py -- a

Writes assets/pkg_microbump_zoom_<letter>.glb. The builders are reused by pkg_microbump_sections.py.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, label, beat, show, key, empty  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import pkg_microbump_detail as K  # noqa: E402
from power_vrm_detail import camera_path, run, rise, bx, join  # noqa: E402

PAGE = "pkg_microbump"
BEATS = 3


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


# ---- builders (return named points; the caller adds tags and camera) ------------------------


def build_ladder(m, root, s=4.0):
    g, pt = K.ladder(m, root, (0.0, 0.0, 0.0), s)
    # current through each joint: one bead stream per joint
    run(root, "ld_c4", [(pt["c4x"], -0.5, 0.3), (pt["c4x"], 2.4 * s, 0.3)], 4, 0.18 * s, m["pwr"], [0, 1, 2], 0.0, 0.8, 50)
    run(root, "ld_ub", [(pt["ubx"], -0.5, 0.3), (pt["ubx"], 1.3 * s, 0.3)], 4, 0.07 * s, m["pwr"], [1, 2], 0.0, 0.8, 40)
    for dx in (-0.4, -0.2, 0.0, 0.2, 0.4):
        run(root, f"ld_hb{dx}", [(pt["hbx"] + dx * s, -0.5, 0.1), (pt["hbx"] + dx * s, 0.4 * s, 0.1)], 2, 0.035 * s, m["pwr"], 2, 0.0, 0.8, 30)
    return pt


def build_assembly(m, root, s=3.0, n=5, melt=True):
    """A row of n joints at scale s: interposer slab with pads, die slab with pillars that gets capped,
    lowered, reflowed and underfilled. Beats: 0 plate + cap, 1 place + reflow, 2 underfill."""
    w = (n * 0.8 + 0.6) * s / 2
    xs = [(i - (n - 1) / 2) * 0.8 * s for i in range(n)]
    lo = empty("as_lo", root)
    p = [bx("as_si", (-w, -1.4 * s, -1.2 * s), (w, -0.4 * s, 0.0), m["si"], lo),
         bx("as_ox", (-w, -0.4 * s, -1.2 * s), (w, -0.06 * s, 0.0), m["oxide"], lo)]
    for x in xs:
        p.append(K.cyl(f"as_pad{x}", x, -0.06 * s, 0.0, 0.0, 0.27 * s, m["copper"], lo, 24, True))
    join(p, "as_lo_mesh")
    die = empty("as_die", root)
    top = 1.20 * s
    d = [bx("as_pi", (-w, top - 0.06 * s, -1.2 * s), (w, top + 0.04 * s, 0.0), m["pi"], die),
         bx("as_beol", (-w, top + 0.04 * s, -1.2 * s), (w, top + 0.4 * s, 0.0), m["beol"], die),
         bx("as_dsi", (-w, top + 0.4 * s, -1.2 * s), (w, top + 1.0 * s, 0.0), m["die"], die)]
    join(d, "as_die_mesh")
    groups = {}
    for state in ("pillar", "cap", "joint"):
        g = empty(f"as_{state}", die)
        parts = []
        for x in xs:
            K.joint(parts, x, 0.0, 0.0, s, g, m, True, state, pad=False)
        join(parts, f"as_{state}_mesh")
        groups[state] = g
    show(groups["pillar"], span(0, 0.0, 0, 0.45))
    show(groups["cap"], span(0, 0.45, 1, 0.55))
    show(groups["joint"], span(1, 0.55, 3, 0.0))
    # beat 0: the die hangs face down above; beat 1 it lowers onto the pads
    K.lower(die, [(F(0, 0.0), 2.2 * s), (F(1, 0.0), 2.2 * s), (F(1, 0.4), 0.0)])
    # plating: copper ions then tin-silver ions drift onto the pillar tips
    for k, x in enumerate(xs):
        run(root, f"as_cu{k}", [(x, -3.0 * s, 0.25 * s), (x, 2.2 * s + 0.6 * s, 0.25 * s)], 3, 0.06 * s, m["copper"], 0, 0.0, 0.3, 30)
        run(root, f"as_sn{k}", [(x, -3.0 * s, 0.25 * s), (x, 2.2 * s + 0.35 * s, 0.25 * s)], 3, 0.06 * s, m["snag"], 0, 0.45, 0.75, 30)
    if melt:
        mg = empty("as_melt", root)
        mp = [bx(f"as_m{x}", (x - 0.24 * s, 0.03 * s, -0.05 * s), (x + 0.24 * s, 0.39 * s, 0.06 * s), m["melt"], mg) for x in xs]
        join(mp, "as_melt_mesh")
        show(mg, span(1, 0.45, 1, 0.7))
        rise(root, "as_heat", (0.0, -1.4 * s, 0.3 * s), 8, 0.08 * s, m["heat"], 1, 0.3, 0.6, 1.6 * s, 40, (w * 0.8, 0.0))
    uf = empty("as_uf", root)
    bx("as_uf_b", (-w - 0.5 * s, 0.0, -1.2 * s), (w, 1.14 * s, -0.04 * s), m["uf"], uf)
    show(uf, span(2, 0.45, 3, 0.0))
    run(root, "as_wick", [(-w - 0.8 * s, 0.6 * s, 0.25 * s), (w, 0.6 * s, 0.25 * s)], 8, 0.08 * s, m["melt"], 2, 0.0, 0.4, 50)
    return {"xs": xs, "w": w, "top": top, "pad": (xs[-1] + 0.27 * s, -0.03 * s, 0.0), "cu": (xs[-1] + 0.2 * s, 0.8 * s, 0.0),
            "sol": (xs[-1] + 0.25 * s, 0.2 * s, 0.0), "die": (w, top + 0.7 * s, 0.0), "uf": (-w, 0.6 * s, 0.0)}


def build_pitch(m, root, s=3.0):
    pitches = [1.0, 0.8, 0.62]
    g, rows = K.bridges(m, root, (0.0, 0.0, 0.0), s, pitches)
    K.glow_bridges(m, root, rows, 2, s, 0.0, "pc_bridge", span(1, 0.3, 2, 0.0))
    # hybrid pads beside, at a fraction of the pitch
    hg, up, hp = K.hybrid(m, root, (rows[0][0][-1] + 6.0 * s, 0.2 * s, 0.0), s * 0.5, "pc_hy", dish=False)
    return rows, hp


def build_stress(m, root, s=1.0):
    """A mini package: substrate in two halves that bow, C4 row, interposer, die on microbumps."""
    sub = []
    for side in (-1, 1):
        g = empty(f"st_sub{side}", root)
        x0, x1 = (-24.0, 0.0) if side < 0 else (0.0, 24.0)
        bx(f"st_abf{side}", (x0, -4.0, -10.0), (x1, -2.4, 0.0), m["abf"], g)
        bx(f"st_core{side}", (x0, -6.4, -10.0), (x1, -4.0, 0.0), m["core"], g)
        sub.append((side, g))
    ip = empty("st_ip", root)
    bx("st_si", (-18.0, 0.0, -10.0), (18.0, 2.4, 0.0), m["si"], ip)
    c4 = empty("st_c4", root)
    xs = K.grid(-16.5, 16.5, 3.0)
    parts = []
    for x in xs:
        parts.append(K.cyl(f"st_c4p{x}", x, -2.5, -2.4, 0.0, 0.9, m["copper"], c4, 16, True))
        o = K.ball(f"st_c4{x}", (x, -1.2, 0.0), 1.15, m["snag"], c4, 20)
        K.cut(o)
        parts.append(o)
    join(parts, "st_c4_mesh")
    die = empty("st_die", root)
    bx("st_beol", (-12.0, 3.6, -10.0), (12.0, 4.2, 0.0), m["beol"], die)
    bx("st_dsi", (-12.0, 4.2, -10.0), (12.0, 6.2, 0.0), m["die"], die)
    ub = empty("st_ub", root)
    parts = []
    for x in K.grid(-11.6, 11.6, 0.8):
        K.joint(parts, x, 2.4, 0.0, 1.0, ub, m, True, "joint")
    join(parts, "st_ub_mesh")
    return {"sub": sub, "xs": xs, "c4": c4}


def bow(sub, b, u0, u1, deg, back=None):
    """Bow the substrate halves by deg (ends up = smile) between u0 and u1 of beat b."""
    for side, g in sub:
        a = math.radians(deg) * side
        key(g, F(b, u0), "rotation_euler", (0.0, 0.0, 0.0), linear=True)
        key(g, F(b, u1), "rotation_euler", (0.0, -a, 0.0), linear=True)
        if back is not None:
            key(g, back[0], "rotation_euler", (0.0, -a, 0.0), linear=True)
            key(g, back[1], "rotation_euler", (0.0, 0.0, 0.0), linear=True)


def build_current(m, root, s=8.0):
    g, pt = K.bench_joint(m, root, (0.0, 0.0, 0.0), s, "cj")
    # electrons flow down (die to interposer), against the conventional current
    for dx in (-0.12, 0.0, 0.12):
        run(root, f"cj_e{dx}", [(dx * s, 1.5 * s, 0.3), (dx * s, -0.9 * s, 0.3)], 6, 0.035 * s, m["gnd_bead"], [0, 1], 0.0, 0.9, 50)
    void = empty("cj_void", root)
    vo = K.cyl("cj_void_c", -0.08 * s, 0.39 * s, 0.415 * s, 0.0, 0.14 * s, m["void"], void, 24)
    key(vo, 0, "scale", (0.02, 0.02, 1.0), linear=True)
    key(vo, F(1, 0.1), "scale", (0.02, 0.02, 1.0), linear=True)
    key(vo, F(1, 0.9), "scale", (1.0, 1.0, 1.0), linear=True)
    show(void, span(1, 0.1, 2, 0.0))
    # beat 2: a row of smaller joints beside, the current split across them
    row = empty("cj_row", root)
    parts = []
    xs = [2.5 * s + 0.4 * s * i for i in range(6)]
    for x in xs:
        K.joint(parts, x, 0.0, 0.0, s * 0.5, row, m, True, "joint")
    parts.append(bx("cj_row_ox", (xs[0] - 0.3 * s, -0.4 * s, -0.5 * s), (xs[-1] + 0.3 * s, -0.03 * s, 0.0), m["oxide"], row))
    parts.append(bx("cj_row_die", (xs[0] - 0.3 * s, 0.6 * s, -0.5 * s), (xs[-1] + 0.3 * s, 1.0 * s, 0.0), m["die"], row))
    join(parts, "cj_row_mesh")
    show(row, span(2, 0.0, 3, 0.0))
    for k, x in enumerate(xs):
        run(root, f"cj_re{k}", [(x, 1.0 * s, 0.3), (x, -0.4 * s, 0.3)], 3, 0.02 * s, m["gnd_bead"], 2, 0.1, 0.9, 50)
    return pt, xs


# ---- zooms --------------------------------------------------------------------------------


def zoom_a(m, root):
    s = 4.0
    pt = build_ladder(m, root, s)
    tags(root, [
        [("C4 BUMP: ~100 um ball", pt["c4"]), ("~150 um pitch", (pt["c4x"], -0.4 * s, 0.0))],
        [("MICROBUMP: ~25 um pillar", pt["ub"]), ("~40 um pitch", (pt["ubx"], -0.4 * s, 0.0))],
        [("HYBRID BOND pads", pt["hb"]), ("<=10 um pitch", (pt["hbx"], -0.4 * s, 0.0)), ("no solder", (pt["hbx"], 0.4 * s, 0.0))],
    ])
    camera_path(root, [
        K.frame((pt["c4x"], 1.2 * s, 0.0), 4.0 * s, 0.18, 0.12),
        K.frame((pt["ubx"], 0.6 * s, 0.0), 2.0 * s, 0.18, 0.10),
        K.frame((-1.0 * s, 0.8 * s, 0.0), 8.0 * s, 0.10, 0.10),
    ])


def zoom_b(m, root):
    s = 3.0
    pt = build_assembly(m, root, s)
    tags(root, [
        [("CU PILLAR plated on the die", (pt["cu"][0], pt["cu"][1] + 2.2 * s, 0.0)), ("tin-silver cap on top", (pt["xs"][0], 2.2 * s + 0.3 * s, 0.0))],
        [("face down onto the pads", pt["die"]), ("REFLOW: ~250 C melts the cap", pt["sol"])],
        [("UNDERFILL wicks in", pt["uf"]), ("cures round every joint", pt["sol"])],
    ])
    camera_path(root, [
        K.frame((0.0, 2.0 * s, 0.0), 5.0 * s, 0.20, 0.08),
        K.frame((0.0, 0.8 * s, 0.0), 4.2 * s, 0.25, 0.10),
        K.frame((0.0, 0.6 * s, -0.4 * s), 4.6 * s, 0.35, 0.22),
    ])


def zoom_c(m, root):
    s = 3.0
    rows, hp = build_pitch(m, root, s)
    tags(root, [
        [("40 um pitch", (rows[0][0][-1] + 0.5 * s, 0.3 * s, rows[0][1])), ("halve the pitch: 4x the joints", (rows[1][0][3], 0.9 * s, rows[1][1]))],
        [("solder bridges", (rows[2][0][3], 0.6 * s, rows[2][1])), ("~10 um: the wall", (rows[2][0][-1] + 0.5 * s, 0.3 * s, rows[2][1]))],
        [("HYBRID BOND: no solder", hp["ox"]), ("copper pads in oxide", hp["cu"])],
    ])
    mid = rows[0][0][3]
    camera_path(root, [
        K.frame((mid, 0.2 * s, -3.0 * s), 8.0 * s, 0.25, 0.45),
        K.frame((rows[2][0][3], 0.3 * s, rows[2][1]), 5.0 * s, 0.25, 0.35),
        K.frame((hp["pads"][2], hp["y"], 0.0), 4.0 * s * 0.5 * 1.4, 0.20, 0.15),
    ])


def zoom_d(m, root):
    st = build_stress(m, root)
    rise(root, "d_heat", (0.0, 6.4, -4.0), 10, 0.3, m["heat"], [0, 1], 0.05, 0.85, 6.0, 50, (10.0, 4.0))
    bow(st["sub"], 1, 0.0, 0.5, 2.0, back=(F(2, 0.1), F(2, 0.5)))
    for x in (st["xs"][0], st["xs"][-1]):
        K.glow_box(m, root, f"d_st{x}", (x - 1.25, -2.4, -0.2), (x + 1.25, 0.0, 0.35), m["stress"], span(1, 0.4, 2, 0.2))
    uf = empty("d_uf", root)
    bx("d_uf_b", (-19.0, -2.4, -10.0), (19.0, 0.0, -0.05), m["uf"], uf)
    show(uf, span(2, 0.15, 3, 0.0))
    tags(root, [
        [("silicon: CTE ~3 ppm/C", (12.0, 5.0, 0.0)), ("organic substrate: ~15+", (20.0, -5.0, 0.0))],
        [("WARPAGE: the substrate bows", (-20.0, -6.0, 0.0)), ("corner joints take the shear", (st["xs"][0], -1.2, 0.4))],
        [("UNDERFILL shares the load", (0.0, -1.2, 0.0)), (">10x thermal-cycle life", (st["xs"][-1], -1.2, 0.4))],
    ])
    camera_path(root, [
        K.frame((0.0, 0.0, 0.0), 50.0, 0.25, 0.20),
        K.frame((-8.0, -2.0, 0.0), 40.0, 0.12, 0.05),
        K.frame((0.0, -1.0, 0.0), 44.0, 0.20, 0.12),
    ])


def zoom_e(m, root):
    s = 8.0
    pt, xs = build_current(m, root, s)
    tags(root, [
        [("electrons flow through the joint", pt["cu"]), ("~1,000s of power bumps per die", pt["die"])],
        [("ELECTROMIGRATION: a void at the IMC", pt["imc1"]), ("current crowds at the corner", pt["ubm"])],
        [("more bumps share the load", (xs[3], 1.1 * s, 0.0)), ("less current each", (xs[-1], 0.5 * s, 0.0))],
    ])
    camera_path(root, [
        K.frame((0.0, 0.3 * s, 0.0), 3.2 * s, 0.20, 0.10),
        K.frame((0.0, 0.42 * s, 0.0), 1.0 * s, 0.15, 0.10),
        K.frame((3.5 * s, 0.45 * s, 0.0), 3.0 * s, 0.15, 0.12),
    ])


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}


def run_zoom(letter):
    name = f"zoom_{letter}"
    m, root = start(name, beats=BEATS, page=PAGE)
    m.update(K.materials())
    ZOOMS[letter](m, root)
    K.finish(root, name, PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in ZOOMS:
        raise SystemExit("usage: blender -b --python pkg_microbump_zooms.py -- <a|b|c|d|e>")
    run_zoom(argv[0])
