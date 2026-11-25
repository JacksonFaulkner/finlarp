"""The ASSEMBLY page's overview (PACKAGING tab), in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_assembly_overview.py

Writes blender/pkg_assembly_overview.blend and assets/pkg_assembly_overview.glb. One beat is 8 s.

One CoWoS-S package, cut open along its front edge (pkg_assembly_detail.py), built step by step on
its 300 mm interposer wafer and then on its substrate.

Beats (match diagrams_nodes/packaging/assembly/overview.rs):
  0 known-good dies    a tray of tested logic dies and HBM stacks; a bad one lights red and is left out
  1 chip on wafer      the bond head lowers the logic die onto the hero site; its microbumps glow as they bond
  2 HBM joins          four stacks land one at a time; every site on the wafer fills
  3 underfill, mold, dice  underfill and mold fill the gaps; the blade runs down the streets; the wafer goes
  4 on substrate       the cut interposer drops onto the substrate; C4 reflow; underfill wicks in from the front
  5 lid and test       TIM and lid; powered up: power climbs, data crosses, heat leaves through the lid
  6 capacity           finished packages ride the line
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, label, beat, show, key  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import pkg_assembly_detail as A  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from pkg_assembly_detail import frame, camera_path, run, present, empty, bx  # noqa: E402

PAGE = "pkg_assembly"
NAME = "overview"
BEATS = 7
HERO = ["c4", "ip", "ub", "uf1", "die", "hbm", "mold"]
LIFT = 26.0


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def mats(m):
    m.update(D.materials())
    m.update(A.materials())
    return m


def tray_beat(m, root, b):
    """The die tray, with good marks on the tested parts and one die failed at sort."""
    t = A.tray(m, root)
    present(t, beat(b))
    good = empty("tray_good", root)
    for i in range(3):
        for j in range(2):
            if (i, j) == (1, 1):
                continue
            x, z = -195.0 + 26.0 * i, -60.0 + 34.0 * j
            bx(f"tg{i}{j}", (x - 8.0, 2.4, z - 11.0), (x + 8.0, 2.6, z + 11.0), m["g_good"], good)
    show(good, span(b, 0.3, b + 1, 0.0))
    bad = empty("tray_bad", root)
    bx("tb", (-177.0, 2.4, -37.0), (-161.0, 2.6, -15.0), m["g_bad"], bad)
    show(bad, span(b, 0.45, b + 1, 0.0))
    return t


def wafer_beats(m, root, b0, b1, cut_at):
    """The wafer and every other site's die (from b0) and stacks (from b0+1), gone at `cut_at`."""
    w = A.wafer(m, root)
    present(w, [(F(b0, 0.0), cut_at)])
    dies = empty("sites_die", root)
    stk = empty("sites_hbm", root)
    for k, (x, z) in enumerate(A.wafer_sites()):
        if z > A.CZ:
            continue
        A.site_kit(m, dies, x, z, f"sd{k}", hbm_on=False)
        A.site_kit(m, stk, x, z, f"sh{k}", die_on=False)
    present(dies, [(F(b0, 0.0), cut_at)])
    present(stk, [(F(b0 + 1, 0.3), cut_at)])
    return w


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    mats(m)
    tray_beat(m, root, 0)
    pk = A.package(m, root)
    L, G = pk["L"], pk["glow"]

    # visibility: hero parts from the step that adds them until the line view (beat 6)
    end = F(6, 0.0)
    A.vis(L, ["ip"], [(F(1, 0.0), end)])
    A.vis(L, ["ub", "die"], [(F(1, 0.0), end)])
    A.vis(L, ["hbm"], [(F(2, 0.0), end)])
    A.vis(L, ["uf1"], [(F(3, 0.12), end)])
    A.vis(L, ["mold"], [(F(3, 0.32), end)])
    A.vis(L, ["c4"], [(F(3, 0.85), end)])
    A.vis(L, ["sub", "bga"], [(F(4, 0.0), end)])
    A.vis(L, ["uf2"], [(F(4, 0.62), end)])
    A.vis(L, ["tim"], [(F(5, 0.0), end)])
    A.vis(L, ["lid"], [(F(5, 0.0), end)])

    # motion: die (with its bumps) falls in beat 1; stacks in beat 2; the cut-out lifts and lands in beat 4
    lift = [(F(4, 0.0), (0.0, 0.0, 0.0)), (F(4, 0.04), (0.0, LIFT, 0.0)), (F(4, 0.12), (0.0, LIFT, 0.0)), (F(4, 0.4), (0.0, 0.0, 0.0))]
    for n in ("die", "ub"):
        A.move(L[n][1], [(F(1, 0.0), (0.0, 30.0, 0.0)), (F(1, 0.15), (0.0, 30.0, 0.0)), (F(1, 0.5), (0.0, 0.0, 0.0))] + lift)
    for n in ("ip", "uf1", "mold", "c4", "hbm"):
        A.move(L[n][1], lift)
    for k, sg in enumerate(pk["hbm"]):
        u = 0.08 + 0.16 * k
        A.move(sg, [(F(2, 0.0), (0.0, 22.0, 0.0)), (F(2, u), (0.0, 22.0, 0.0)), (F(2, u + 0.14), (0.0, 0.0, 0.0))])
    # bond head carrying the die
    nz = A.nozzle(m, root)
    nzm = empty("nz_mov", root)
    nz.parent = nzm
    present(nzm, span(1, 0.0, 1, 0.75))
    top = A.DIE_Y[1]
    A.move(nz, [(F(1, 0.0), (0.0, top + 30.0, -12.0)), (F(1, 0.15), (0.0, top + 30.0, -12.0)), (F(1, 0.5), (0.0, top, -12.0)),
                (F(1, 0.6), (0.0, top, -12.0)), (F(1, 0.74), (0.0, top + 40.0, -12.0))])
    show(G["ub"], span(1, 0.52, 1, 0.8) + span(2, 0.75, 2, 0.95))
    # beat 3: dicing blade down the streets either side of the hero
    for s in (-1, 1):
        bg, _ = A.blade(m, root, name=f"bl{s}")
        bm = empty(f"bl{s}_mov", root)
        bg.parent = bm
        present(bm, span(3, 0.45, 3, 0.85))
        xs = s * A.SITE / 2
        A.move(bg, [(F(3, 0.45), (xs, A.RDL_Y[1] + 20.0, -300.0)), (F(3, 0.82), (xs, A.RDL_Y[1] + 20.0, 20.0))])
    wafer_beats(m, root, 1, 6, F(3, 0.85))
    # beat 4: reflow and underfill
    show(G["c4"], span(4, 0.4, 4, 0.58))
    nd = A.needle(m, root)
    ndm = empty("nd_mov", root)
    nd.parent = ndm
    present(ndm, span(4, 0.55, 4, 0.9))
    y = A.C4_Y[1] + 0.4
    A.move(nd, [(F(4, 0.55), (-A.IP_X, y, 2.0)), (F(4, 0.85), (A.IP_X, y, 2.0))])
    uf = L["uf2"][1]
    for f, s in ((F(4, 0.0), 0.02), (F(4, 0.62), 0.02), (F(4, 0.95), 1.0)):
        key(uf, f, "scale", (1.0, s, 1.0))
    # beat 5: lid, then powered up
    A.drop(L, "tim", 5, 0.0, 0.15, h=12.0, hold_from=5)
    A.drop(L, "lid", 5, 0.1, 0.32, h=22.0, hold_from=5)
    A.flows(m, root, "ov", [5], u0=0.35, u1=0.9, n=4)
    show(G["die"], span(5, 0.4, 6, 0.0))
    # beat 6: the line
    cv = A.conveyor(m, root, 200.0, 560.0, -40.0, 0.0)
    present(cv, beat(6))
    line = empty("line", root)
    present(line, beat(6))
    for k in range(6):
        g = A.mini_package(m, line, 0.0, -4.0, f"mp{k}")
        x0 = 190.0 + 64.0 * k
        A.move(g, [(F(6, 0.0), (x0, 0.0, 0.0)), (F(6, 0.99), (x0 + 40.0, 0.0, 0.0))])

    tags = {
        0: [("only KNOWN-GOOD DIES", (-169.0, 2.6, -60.0)), ("HBM stacks, tested", (-108.0, 5.0, -44.0)),
            ("failed at wafer sort", (-169.0, 2.6, -26.0))],
        1: [("300 mm interposer wafer", (-180.0, A.RDL_Y[1], -160.0)), ("CHIP ON WAFER: bond head", (0.0, A.DIE_Y[1] + 30.0, -24.0)),
            ("microbumps bond", (-10.0, A.UB_Y[1], 0.0))],
        2: [("HBM stacks join", (A.HBM_X[1], A.DIE_Y[1], -8.0)), ("logic die", (-8.0, A.DIE_Y[1], -20.0)),
            ("every site on the wafer", (92.0, A.DIE_Y[1], -32.0))],
        3: [("UNDERFILL + mold", (A.DIE_X + 1.5, A.DIE_Y[1], -2.0)), ("dicing blade", (A.SITE / 2, A.RDL_Y[1] + 40.0, -100.0)),
            ("cut along the streets", (-A.SITE / 2, A.RDL_Y[1], -150.0))],
        4: [("ON SUBSTRATE", (-40.0, A.SUB_Y[1], -60.0)), ("C4 REFLOW", (-36.0, 6.0, 0.0)), ("UNDERFILL FLOW", (0.0, 7.0, 2.0))],
        5: [("TIM + lid", (-40.0, A.LID_Y[1], -20.0)), ("TEST: power in", (-44.0, -8.0, 0.7)), ("heat out the top", (0.0, 32.0, -8.0))],
        6: [("CAPACITY: wafers a month", (300.0, 6.0, -10.0)), ("one 300 mm wafer: ~15-20 big packages", (420.0, 6.0, -10.0))],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))

    camera_path(root, [
        frame((-150.0, 0.0, -40.0), 150.0, 0.30, 0.55),
        [(0.0 + D.GLIDE, frame((0.0, 9.0, -140.0), 520.0, 0.20, 0.75, pad=1.0)), (0.45, frame((0.0, 10.0, -20.0), 110.0, 0.30, 0.40))],
        frame((10.0, 10.0, -30.0), 130.0, 0.35, 0.45),
        [(D.GLIDE, frame((0.0, 10.0, -10.0), 110.0, 0.30, 0.25)), (0.45, frame((0.0, 9.0, -130.0), 420.0, 0.25, 0.70, pad=1.0))],
        [(D.GLIDE, frame((0.0, 4.0, -20.0), 140.0, 0.30, 0.35)), (0.5, frame((0.0, 5.0, -2.0), 110.0, 0.15, 0.16))],
        frame((0.0, 10.0, -4.0), 120.0, 0.18, 0.18),
        frame((360.0, 2.0, -20.0), 260.0, 0.30, 0.40),
    ])
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
