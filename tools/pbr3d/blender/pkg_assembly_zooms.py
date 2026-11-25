"""Zoom-ins (a-e) for the ASSEMBLY page: the cut-open CoWoS-S package (pkg_assembly_detail.py) with
its own camera, motion, beads and tags, three beats each (diagrams_nodes/packaging/assembly/zooms.rs):

  a chip on wafer     bumps on the die face; thermocompression bond; HBM joins and data crosses the RDL
  b mold and thin     underfill wicks and mold fills; the wafer is ground thin; TSVs revealed, C4 bumps grown
  c dice + substrate  the blade cuts the street; the interposer drops onto the substrate; C4 reflow + underfill
  d lid               TIM on the die and stacks; the lid glued on; heat leaves through it
  e test and yield    probe card on the wafer (known-good die); final test socket; ten parts multiply

Run one zoom per Blender process:

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_assembly_zooms.py -- a

Writes assets/pkg_assembly_zoom_<letter>.glb (and blender/pkg_assembly_zoom_<letter>.blend).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show, key, pivot, rel  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import pkg_assembly_detail as A  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from pkg_assembly_detail import frame, camera_path, run, present, empty, bx  # noqa: E402

PAGE = "pkg_assembly"
BEATS = 3
END = F(BEATS, 0)


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def after(b, u):
    return [(F(b, u), END)]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def mats(m):
    m.update(D.materials())
    m.update(A.materials())
    return m


def tool(build, m, root, name, iv, keys):
    """A tool group, shown during `iv`, moved by `keys` [(frame, offset)]."""
    mv = empty(f"{name}_mv", root)
    g = build(m, mv)
    g = g[0] if isinstance(g, tuple) else g
    present(mv, iv)
    A.move(g, keys)
    return g


def wick(L, name, f0, f1):
    """Underfill `name` creeps in from the front edge (z = 0) toward the back."""
    mv = L[name][1]
    for f, s in ((0, 0.02), (f0, 0.02), (f1, 1.0)):
        key(mv, f, "scale", (1.0, s, 1.0))


def zoom_a(m, root):
    pk = A.package(m, root, ["ip", "ub", "die", "hbm"])
    L, G = pk["L"], pk["glow"]
    w = A.wafer(m, root)
    present(w, after(0, 0.0))
    A.vis(L, ["ip", "ub", "die"], after(0, 0.0))
    A.vis(L, ["hbm"], after(2, 0.0))
    for n in ("die", "ub"):
        A.move(L[n][1], [(0, (0.0, 9.0, 0.0)), (F(1, 0.1), (0.0, 9.0, 0.0)), (F(1, 0.45), (0.0, 0.0, 0.0))])
    tool(A.nozzle, m, root, "nz", span(0, 0.0, 1, 0.8),
         [(0, (0.0, A.DIE_Y[1] + 9.0, -12.0)), (F(1, 0.1), (0.0, A.DIE_Y[1] + 9.0, -12.0)), (F(1, 0.45), (0.0, A.DIE_Y[1], -12.0)),
          (F(1, 0.62), (0.0, A.DIE_Y[1], -12.0)), (F(1, 0.8), (0.0, A.DIE_Y[1] + 40.0, -12.0))])
    show(G["ub"], span(1, 0.45, 1, 0.75))
    for k, sg in enumerate(pk["hbm"]):
        u = 0.02 + 0.1 * k
        A.move(sg, [(0, (0.0, 14.0, 0.0)), (F(2, u), (0.0, 14.0, 0.0)), (F(2, u + 0.12), (0.0, 0.0, 0.0))])
    for s in (-1, 1):
        run(root, f"a_sig{s}", A.sig_path(s), 6, 0.35, m["g_sig"], 2, 0.45, 0.92, 40)
    tags(root, [
        [("copper pillar + solder cap", (6.0, A.UB_Y[0] + 9.6, 0.0)), ("die face down: BEOL metal", (-8.0, 12.0 + 9.0, 0.0)),
         ("interposer RDL pads", (-20.0, A.RDL_Y[1], 0.0))],
        [("bond head: heat + force", (0.0, A.DIE_Y[1] + 6.0, -14.0)), ("THERMOCOMPRESSION BOND", (-6.0, A.UB_Y[1], 0.0)),
         ("~40 um pitch", (8.0, A.UB_Y[0], 0.0))],
        [("HBM stacks join", (A.HBM_X[1], A.DIE_Y[1], -6.0)), ("1,024 data wires per stack", (17.0, 10.46, 0.0)),
         ("still on the wafer", (60.0, A.RDL_Y[1], -40.0))],
    ])
    camera_path(root, [
        frame((-4.0, 14.0, 0.0), 40.0, 0.25, 0.15, min_d=44.0),
        frame((0.0, 13.0, -8.0), 70.0, 0.30, 0.30),
        frame((12.0, 11.5, 0.0), 44.0, 0.22, 0.14, min_d=46.0),
    ])


def zoom_b(m, root):
    pk = A.package(m, root, ["c4", "ip", "ub", "uf1", "die", "hbm", "mold"])
    L, G = pk["L"], pk["glow"]
    A.vis(L, ["ip", "ub", "die", "hbm"], after(0, 0.0))
    A.vis(L, ["uf1"], after(0, 0.05))
    A.vis(L, ["mold"], after(0, 0.55))
    A.vis(L, ["c4"], after(2, 0.3))
    wick(L, "uf1", F(0, 0.05), F(0, 0.5))
    A.drop(L, "mold", 0, 0.55, 0.8, h=10.0)
    tool(A.needle, m, root, "nd", span(0, 0.0, 0, 0.5),
         [(0, (-A.DIE_X, A.UB_Y[1] + 0.3, 1.5)), (F(0, 0.05), (-A.DIE_X, A.UB_Y[1] + 0.3, 1.5)), (F(0, 0.45), (A.DIE_X, A.UB_Y[1] + 0.3, 1.5))])
    # beat 1: the wafer starts thick; the wheel grinds it back from below to the TSV tips
    bulk = empty("bulk_vis", root)
    present(bulk, [(0, F(1, 0.8))])
    pv = pivot("bulk_pv", (0.0, A.IP_Y[0], 0.0), bulk)
    bx("bulk", rel((0.0, A.IP_Y[0], 0.0), (-A.IP_X, A.IP_Y[0] - 8.0, A.IP_Z)), rel((0.0, A.IP_Y[0], 0.0), (A.IP_X, A.IP_Y[0], 0.0)), m["a_si"], pv)
    for f, s in ((0, 1.0), (F(1, 0.15), 1.0), (F(1, 0.75), 0.02)):
        key(pv, f, "scale", (1.0, 1.0, s))
    gr = tool(A.grinder, m, root, "gr", span(1, 0.0, 1, 0.9),
              [(F(1, 0.0), (0.0, A.IP_Y[0] - 40.0, -32.0)), (F(1, 0.15), (0.0, A.IP_Y[0] - 8.0 - 6.0, -32.0)),
               (F(1, 0.75), (0.0, A.IP_Y[0] - 6.0, -32.0)), (F(1, 0.9), (0.0, A.IP_Y[0] - 40.0, -32.0))])
    gr.rotation_mode = "XYZ"
    gr.rotation_euler = (3.14159, 0.0, 0.0)  # wheel face up, spindle down
    A.drop(L, "c4", 2, 0.3, 0.55, h=-3.0)
    show(G["c4"], span(2, 0.55, 2, 0.8))
    tags(root, [
        [("UNDERFILL wicks under", (0.0, A.UB_Y[0], 0.0)), ("needle", (-A.DIE_X, A.UB_Y[1] + 10.0, 1.5)), ("MOLD fills the gaps", (A.DIE_X + 1.5, A.DIE_Y[1], -1.0))],
        [("~775 um wafer", (-30.0, A.IP_Y[0] - 4.0, 0.0)), ("back-grind wheel", (0.0, A.IP_Y[0] - 16.0, -10.0)),
         ("down to ~100 um", (20.0, A.IP_Y[0], 0.0))],
        [("TSV tips revealed", (-14.0, A.IP_Y[0], 0.0)), ("C4 bumps grown", (-30.0, 6.0, 0.0)), ("~130 um bumps", (24.0, 6.0, 0.0))],
    ])
    camera_path(root, [
        frame((0.0, 12.0, 0.0), 60.0, 0.25, 0.25),
        frame((-10.0, 4.0, -4.0), 90.0, 0.30, -0.12),
        frame((-20.0, 7.0, 0.0), 44.0, 0.20, 0.06, min_d=46.0),
    ])


def zoom_c(m, root):
    pk = A.package(m, root)
    L, G = pk["L"], pk["glow"]
    hero = ["c4", "ip", "ub", "uf1", "die", "hbm", "mold"]
    A.vis(L, hero, after(0, 0.0))
    A.vis(L, ["sub", "bga"], after(1, 0.0))
    A.vis(L, ["uf2"], after(2, 0.45))
    A.vis(L, ["tim", "lid"], [])
    w = A.wafer(m, root)
    present(w, span(0, 0.0, 0, 0.85))
    nb = empty("nbr", root)
    A.site_kit(m, nb, A.SITE, A.CZ, "nb")
    present(nb, span(0, 0.0, 0, 0.85))
    tool(A.blade, m, root, "bl", span(0, 0.0, 0, 0.85),
         [(0, (A.SITE / 2, A.RDL_Y[1] + 21.0, -140.0)), (F(0, 0.1), (A.SITE / 2, A.RDL_Y[1] + 21.0, -140.0)),
          (F(0, 0.8), (A.SITE / 2, A.RDL_Y[1] + 21.0, 30.0))])
    run(root, "c_kerf", [(A.SITE / 2, A.RDL_Y[1] + 0.5, -100.0), (A.SITE / 2 + 2.0, A.RDL_Y[1] + 6.0, 6.0)], 10, 0.4, m["a_solder"], 0, 0.15, 0.75, 30)
    lift = [(0, (0.0, 0.0, 0.0)), (F(0, 0.88), (0.0, 0.0, 0.0)), (F(0, 0.98), (0.0, 22.0, 0.0)), (F(1, 0.2), (0.0, 22.0, 0.0)), (F(1, 0.6), (0.0, 0.0, 0.0))]
    for n in hero:
        A.move(L[n][1], lift)
    show(G["c4"], span(1, 0.6, 1, 0.95))
    wick(L, "uf2", F(2, 0.45), F(2, 0.9))
    tool(A.needle, m, root, "nd", span(2, 0.0, 2, 0.9),
         [(F(2, 0.0), (-A.IP_X, A.C4_Y[1] + 0.4, 2.0)), (F(2, 0.4), (-A.IP_X, A.C4_Y[1] + 0.4, 2.0)), (F(2, 0.85), (A.IP_X, A.C4_Y[1] + 0.4, 2.0))])
    tags(root, [
        [("DICING blade", (A.SITE / 2, A.RDL_Y[1] + 40.0, -30.0)), ("scribe street", (A.SITE / 2, A.RDL_Y[1], -60.0)),
         ("next site", (A.SITE, A.DIE_Y[1], -20.0))],
        [("ON SUBSTRATE", (-30.0, A.SUB_Y[1], -40.0)), ("C4 REFLOW: ~250 C", (-34.0, 6.0, 0.0)), ("ABF build-up + core", (-50.0, 0.0, 0.0))],
        [("UNDERFILL FLOW", (0.0, 6.0, 1.0)), ("capillary: front to back", (30.0, 6.0, -30.0)), ("needle", (0.0, A.C4_Y[1] + 14.0, 2.0))],
    ])
    camera_path(root, [
        frame((40.0, 10.0, -20.0), 130.0, 0.35, 0.45),
        frame((0.0, 6.0, -10.0), 120.0, 0.25, 0.20),
        frame((0.0, 5.0, -10.0), 110.0, 0.20, 0.28),
    ])


def zoom_d(m, root):
    pk = A.package(m, root)
    L, G = pk["L"], pk["glow"]
    A.vis(L, [n for n in A.ORDER if n not in ("tim", "lid")], after(0, 0.0))
    A.vis(L, ["tim"], after(0, 0.2))
    A.vis(L, ["lid"], after(1, 0.0))
    A.drop(L, "tim", 0, 0.2, 0.55, h=8.0)
    A.drop(L, "lid", 1, 0.2, 0.6, h=26.0)
    show(G["die"], after(2, 0.0))
    for x in (-24.0, -10.0, 0.0, 10.0, 24.0):
        run(root, f"d_ht{x:+.0f}", A.heat_path(x, z=-4.0), 3, 0.9, m["g_heat"], 2, 0.05, 0.8, 60)
    tags(root, [
        [("TIM: indium sheet", (0.0, A.TIM_Y[1], -10.0)), ("die + HBM level: one height", (A.HBM_X[1], A.DIE_Y[1], -2.0))],
        [("copper LID", (-30.0, A.LID_Y[1], -20.0)), ("adhesive to substrate", (-A.LID_X + 2.0, A.SUB_Y[1], 0.0)),
         ("stiffens against warpage", (A.LID_X - 2.0, 10.0, 0.0))],
        [("~1,000 W out the top", (0.0, 32.0, -4.0)), ("die -> TIM -> lid", (-12.0, A.TIM_Y[1], 0.0)), ("cold plate goes here", (20.0, A.LID_Y[1], -40.0))],
    ])
    camera_path(root, [
        frame((0.0, 14.0, -12.0), 90.0, 0.30, 0.35),
        frame((0.0, 10.0, -10.0), 130.0, 0.30, 0.25),
        frame((0.0, 18.0, -4.0), 110.0, 0.15, 0.15),
    ])


def zoom_e(m, root):
    pk = A.package(m, root)
    L, G = pk["L"], pk["glow"]
    # beat 0: probe card on a die still on its wafer (wafer sort); beats 1-2: the finished package
    A.vis(L, [n for n in A.ORDER if n != "ip"], after(1, 0.0))
    A.vis(L, ["ip"], [])
    dw_v = empty("sort_die_v", root)
    dw = empty("sort_die", dw_v)
    bx("sd_si", (-A.DIE_X, 0.0, A.DIE_Z), (A.DIE_X, 3.0, 0.0), m["a_die"], dw)
    bx("sd_beol", (-A.DIE_X, 3.0, A.DIE_Z), (A.DIE_X, 3.8, 0.0), m["a_beol"], dw)
    bx("sd_wf", (-90.0, -2.0, -120.0), (90.0, 0.0, 0.0), m["a_wafer"], dw)
    for i, x in enumerate((-60.0, 60.0)):
        bx(f"sd_n{i}", (x - A.DIE_X, 0.0, A.DIE_Z), (x + A.DIE_X, 3.8, 0.0), m["a_die"], dw)
    A.move(dw, [(0, (0.0, 30.0, 0.0))])
    present(dw_v, span(0, 0.0, 1, 0.0))
    pc = tool(lambda mm, p: A.probe_card(mm, p, -A.DIE_X + 1.0, A.DIE_X - 1.0, A.DIE_Z + 1.0, -1.0, 0.0), m, root, "pc", beat(0),
              [(0, (0.0, 30.0 + 3.8 + 10.0, 0.0)), (F(0, 0.15), (0.0, 30.0 + 3.8 + 10.0, 0.0)), (F(0, 0.35), (0.0, 33.8, 0.0))])
    for k, x in enumerate((-10.0, -3.0, 4.0, 11.0)):
        run(root, f"e_pr{k}", [(x, 33.8 + 16.0, -6.0), (x, 33.8 + 6.0, -6.0), (x, 33.8, -6.0), (x * 0.5, 33.8 - 0.4, -6.0)], 3, 0.5, m["g_probe"], 0, 0.4, 0.9, 30)
    good = empty("sd_good", root)
    bx("sd_g", (-A.DIE_X, 33.8 + 0.05, A.DIE_Z), (A.DIE_X, 33.9, 0.3), m["g_good_a"], good)
    show(good, span(0, 0.8, 1, 0.0))
    sk = empty("sk_mv", root)
    A.socket(m, sk)
    present(sk, beat(1))
    A.flows(m, root, "e", [1], u0=0.1, u1=0.85, n=4)
    show(G["die"], span(1, 0.3, 2, 0.0))
    marks = A.yield_marks(m, root, m["g_good_a"])
    for k, g in enumerate(marks):
        end = F(2, 0.72)
        show(g, [(F(2, 0.04 + 0.06 * k), end)])
    bad = A.yield_marks(m, root, m["g_bad_a"], name="yb")
    for g in bad:
        show(g, after(2, 0.74))
    tags(root, [
        [("probe card", (0.0, 50.0, -20.0)), ("WAFER SORT: die by die", (-10.0, 33.8, 0.0)), ("pass: KNOWN-GOOD DIE", (12.0, 33.8, -10.0))],
        [("final TEST socket", (-A.SUB_X - 6.0, -6.0, 0.0)), ("pogo pins on every ball", (-30.0, -12.0, -1.0)), ("run at speed, hot", (0.0, A.LID_Y[1], -20.0))],
        [("10 parts x 99% = ~90%", (0.0, A.LID_Y[1], -10.0)), ("YIELD STACKUP", (-A.SUB_X, 0.0, 0.3)), ("one fails: all scrapped", (A.SUB_X, 12.0, 0.3))],
    ])
    camera_path(root, [
        frame((0.0, 38.0, -22.0), 120.0, 0.45, 0.28),
        frame((0.0, 0.0, -16.0), 150.0, 0.30, 0.25),
        frame((0.0, 4.0, -2.0), 125.0, 0.10, 0.10),
    ])


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}


def run_zoom(letter):
    name = f"zoom_{letter}"
    m, root = start(name, beats=BEATS, page=PAGE)
    mats(m)
    ZOOMS[letter](m, root)
    finish(name, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in ZOOMS:
        raise SystemExit("usage: blender -b --python pkg_assembly_zooms.py -- <a|b|c|d|e>")
    run_zoom(argv[0])
