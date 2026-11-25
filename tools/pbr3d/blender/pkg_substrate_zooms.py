"""Zoom-ins (a-e) for the SUBSTRATE page: the overview's cut-open substrate
(pkg_substrate_detail.scene) with its own camera, motion, beads and tags, three beats each
(diagrams_nodes/packaging/substrate/zooms.rs):

  a building the layers       the bare core and its PTHs; build-up layers laminate on; resist + bumps
  b fan-out: C4 to BGA        the bump field; signals cross a layer; they land on board-pitch balls
  c warpage                   flat when cold; bowed in reflow; bowed the other way cooled, joints strained
  d ABF film and its makers   a roll of film on its carrier; the film in every layer; who makes it
  e power fans in             up from the balls; across the planes; into the die, caps beside

Run one zoom per Blender process:

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_substrate_zooms.py -- a

Writes assets/pkg_substrate_zoom_<letter>.glb.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, label, beat, show, key  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import pkg_substrate_detail as D  # noqa: E402
from pkg_substrate_detail import frame, camera_path, run, rise, present, empty, bead  # noqa: E402
import pkg_substrate_overview as OV  # noqa: E402

PAGE = "pkg_substrate"
BEATS = 3
BY = 400.0


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def after(b, u):
    return [(F(b, u), F(BEATS, 0))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def drop_in(obj, f0, f1, h=30.0):
    """Lower a group onto its place from h above between frames f0 and f1."""
    key(obj, f0, "location", P(0.0, h, 0.0), linear=True)
    key(obj, f1, "location", P(0.0, 0.0, 0.0), linear=True)


def build_order(s, b_core, b_layers, b_rest):
    """Present the substrate in build order: core alone in b_core; layers k = 0..5 each side
    dropping in through beat b_layers; routes, resist and bumps from b_rest."""
    sub = s["sub"]
    for side in ("top", "bot"):
        for k, lg in enumerate(sub[f"{side}_layers"]):
            u = 0.08 + 0.13 * k
            sign = 1 if side == "top" else -1
            inner = empty(f"{lg.name}_drop", lg.parent)
            lg.parent = inner
            present(inner, after(b_layers, u))
            drop_in(lg, F(b_layers, u), F(b_layers, u + 0.1), 24.0 * sign)
    for k in ("routes",):
        present(sub[k], after(b_rest, 0.0))
    for k in ("top_sr", "bot_sr"):
        g = empty(f"{k}_g", sub[k].parent)
        sub[k].parent = g
        present(g, after(b_rest, 0.1))
    for k in ("c4", "bga", "caps"):
        present(s[k], after(b_rest, 0.3))
    present(s["pkg"]["group"], after(b_rest, 0.55))


def zoom_a(m, root, s):
    build_order(s, 0, 1, 2)
    tags(root, [
        [("CORE: glass cloth + epoxy", D.A_CORE), ("drilled, plated through-holes", D.A_PTH), ("copper foil each face", (-60.0, D.CORE1, 0.0))],
        [("ABF film laminated on", (-60.0, D.CORE1 + 4.0, 0.0)), ("copper plated, patterned", (-90.0, D.mid(D.cu_y(1, 2)), 0.0)),
         ("both sides at once", (-60.0, D.CORE0 - 4.0, 0.0))],
        [("laser microvias stacked", (D.ROUTES[0][0], D.mid((D.CORE1, D.TOP)), 0.0)), ("solder resist + pads", D.A_SR),
         ("bumps go on last", D.A_C4)],
    ])
    camera_path(root, [
        frame((-80.0, 31.0, 0.0), 120.0, 0.18, 0.10),
        frame((-60.0, 31.0, 0.0), 150.0, 0.25, 0.14),
        [(0.0, frame((-40.0, 34.0, 0.0), 170.0, 0.25, 0.16)), (0.5, frame((20.0, 50.0, 0.0), 120.0, 0.10, 0.14))],
    ])


def zoom_b(m, root, s):
    show(s["sub"]["lit"], span(1, 0.0, 3, 0.0))
    OV.signal_beads(m, root, s, [0], n=2, u0=0.3, u1=0.8)
    OV.signal_beads(m, root, s, [1, 2], n=4)
    tags(root, [
        [("C4 pitch ~150 um", (D.C4_PITCH * 3, D.C4_Y, 0.0)), ("tens of thousands of bumps", (-24.0, D.C4_Y, -40.0)),
         ("resist openings", D.A_SR)],
        [("down a microvia stack", (D.ROUTES[2][0], D.mid((D.CORE1, D.TOP)), 0.0)), ("across one signal layer", (96.0, D.mid(D.cu_y(1, 4)), 0.0)),
         ("deeper bumps, deeper layers", (40.0, D.mid(D.cu_y(1, 0)), 0.0))],
        [("through the core", (120.0, D.CORE0 + 6.0, 0.0)), ("BGA pitch ~1 mm", (96.0, D.BGA_Y, 0.0)),
         ("about 7x wider", (144.0, D.BGA_Y, 0.0))],
    ])
    camera_path(root, [
        frame((24.0, 66.0, -20.0), 90.0, 0.25, 0.55),
        D.V_FACE_R,
        frame((100.0, 10.0, 0.0), 110.0, -0.20, 0.02),
    ])


def zoom_c(m, root, s):
    OV.hide_main(s, [])
    g, piv = OV.warp_scene(m, root, [0, 1, 2], [(F(0, 0.0), 0.0), (F(1, 0.1), 0.0), (F(1, 0.5), -0.2),
                                                (F(2, 0.0), -0.2), (F(2, 0.4), 0.16)])
    rise(root, "c_heat", (0.0, D.TOP, -40.0), 10, 1.3, m["heat"], 1, 0.05, 0.8, 40.0, 60, (120.0, 30.0))
    D.show_strain(g, after(2, 0.45))
    tags(root, [
        [("flat when cool", (0.0, D.TOP + 4.0, 0.0)), ("copper and resin expand differently", D.A_TOPBU)],
        [("reflow ~250 C: it bows", (0.0, D.TOP + 4.0, 0.0)), ("middle high, ends low", (130.0, D.TOP - 20.0, 0.0))],
        [("cooled: bows back", (0.0, D.TOP + 4.0, 0.0)), ("corner joints strain", (150.0, -D.BGA_R, 0.0))],
    ])
    camera_path(root, [
        frame((0.0, 20.0, -40.0), 330.0, 0.10, 0.10, pad=1.0),
        frame((0.0, 20.0, -40.0), 330.0, 0.20, 0.08, pad=1.0),
        frame((90.0, 10.0, -10.0), 160.0, -0.25, 0.05),
    ])


def zoom_d(m, root, s):
    rg = D.abf_roll(m, root, (0.0, BY, 0.0), 1.0, "d_roll")
    present(rg, span(0, 0.0, 1, 0.0))
    bg, who = D.share_bars(m, root, (0.0, BY, 0.0), 1.0, "d_bars")
    present(bg, beat(2))
    tags(root, [
        [("ABF: epoxy film, no glass cloth", (40.0, BY + 5.0, -20.0)), ("PET carrier under it", (-50.0, BY + 1.0, 0.0)),
         ("cover film on top", (20.0, BY + 6.0, -30.0)), ("one film maker: Ajinomoto", (0.0, BY + 40.0, -60.0))],
        [("ABF between every copper layer", (48.0, D.mid(D.abf_y(1, 3)), 0.0)), ("smooth: fine lines plate on it", (80.0, D.mid(D.abf_y(1, 5)), 0.0)),
         ("~95% of GPU-grade film (est.)", D.A_TOPBU)],
        [(f"{w}", p) for w, p in who.items()] + [("FC-BGA share, % (est.)", (0.0, BY + 116.0, -12.0))],
    ])
    camera_path(root, [
        frame((0.0, BY + 18.0, -30.0), 150.0, 0.35, 0.32),
        D.V_TOPBU,
        frame((0.0, BY + 50.0, -12.0), 190.0, 0.15, 0.18, pad=1.0),
    ])


def zoom_e(m, root, s):
    show(s["lit_planes"], span(1, 0.2, 3, 0.0))
    OV.power_beads(m, root, [0], n=4, u1=0.6)
    OV.power_beads(m, root, [1, 2], n=6)
    rise(root, "e_heat", (0.0, D.DIE_Y[1] + 1.0, -30.0), 6, 1.4, m["heat"], 2, 0.3, 0.9, 40.0, 70, (24.0, 20.0))
    tags(root, [
        [("~0.8 V from the board", (24.0, D.BGA_Y, 0.0)), ("hundreds of power balls", (-24.0, D.BGA_Y, 0.0)),
         ("up a plated through-hole", (16.0, D.CORE0 + 8.0, 0.0))],
        [("ground / power planes", D.A_PLANE), ("solid copper spreads the current", (40.0, D.mid(D.cu_y(1, 3)), 0.0)),
         ("antipads let signals pass", (D.ROUTES[0][0], D.mid(D.cu_y(1, 1)), 0.0))],
        [("into the bumps and die", D.A_DIE), ("land-side caps: a charge reserve", D.A_CAP), ("1,000+ A on GPU packages", (-30.0, D.TOP, 0.0))],
    ])
    camera_path(root, [
        frame((10.0, 10.0, 0.0), 110.0, 0.20, 0.02),
        frame((0.0, 40.0, 0.0), 160.0, 0.15, 0.16),
        frame((0.0, 50.0, -10.0), 150.0, 0.30, 0.30),
    ])


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}


def run_zoom(letter):
    name = f"zoom_{letter}"
    m, root = start(name, beats=BEATS, page=PAGE)
    m.update(D.materials())
    s = D.scene(m, root)
    ZOOMS[letter](m, root, s)
    finish(name, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in ZOOMS:
        raise SystemExit("usage: blender -b --python pkg_substrate_zooms.py -- <a|b|c|d|e>")
    run_zoom(argv[0])
