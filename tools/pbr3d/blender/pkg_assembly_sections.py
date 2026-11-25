"""The ASSEMBLY page's nine numbered sections, in the picture-and-panel template (docs/diagram-pages.md).
Section N illustrates heading N of tui/src/screens/diagrams_pages/PKG_ASSEMBLY.txt (the tenth, Sources,
is text only). Three beats each, one beat is 8 s.

Run one section per Blender process:

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_assembly_sections.py -- <n>

Writes blender/pkg_assembly_section_<n>.blend and assets/pkg_assembly_section_<n>.glb. The package and
the tools come from pkg_assembly_detail.py.

  1 what happens   chip on wafer; cut apart; on substrate
  2 the parts      the substrate, C4 and BGA; the interposer, TSVs, RDL, microbumps; die, HBM, mold, TIM, lid
  3 in order       exploded stack assembling: place + bond; underfill, mold, thin; substrate, underfill, lid
  4 yield          one part at 99%; ten parts multiply to ~90%; one fails and the whole package goes
  5 capacity       one wafer, ~15-20 big interposers; smaller ones fit more; the line is the limit
  6 OSAT           TSMC does chip on wafer; the wafer ships; an OSAT does on-substrate and test
  7 test           wafer sort; after chip on wafer; final test in a socket
  8 who makes it   exploded package, makers tagged per layer
  9 chokepoints    capacity queue; warpage at reflow; a late defect scraps it all
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, label, beat, show, key  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import pkg_assembly_detail as A  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from pkg_assembly_detail import frame, camera_path, run, present, empty, bx  # noqa: E402
from pkg_assembly_zooms import span, after, tags, mats, tool, wick, END  # noqa: E402

PAGE = "pkg_assembly"
BEATS = 3
HERO = ["c4", "ip", "ub", "uf1", "die", "hbm", "mold"]
ALL = A.ORDER

V_WHOLE = frame((0.0, 4.0, -26.0), 130.0, 0.30, 0.38)
V_FACE = frame((0.0, 4.0, -2.0), 122.0, 0.10, 0.10)
V_SUB = frame((-24.0, -1.0, 0.0), 80.0, 0.18, 0.12)
V_IP = frame((-20.0, 9.0, 0.0), 56.0, 0.20, 0.12)
V_TOP = frame((16.0, 14.0, 0.0), 50.0, 0.22, 0.14, min_d=50.0)


def explode_keys(names, gap, b, u0, u1, start_exploded=True):
    """Offsets for an exploded stack collapsing (or opening) over [u0, u1] of beat b."""
    out = {}
    for k, n in enumerate(names):
        h = gap * k
        a, z = (h, 0.0) if start_exploded else (0.0, h)
        out[n] = [(0, (0.0, a, 0.0)), (F(b, u0), (0.0, a, 0.0)), (F(b, u1), (0.0, z, 0.0))]
    return out


# ---- 1 what happens -------------------------------------------------------------------------------


def sec1(m, root):
    pk = A.package(m, root)
    L, G = pk["L"], pk["glow"]
    A.vis(L, HERO, after(0, 0.0))
    A.vis(L, ["sub", "bga"], after(2, 0.0))
    A.vis(L, ["uf2"], after(2, 0.6))
    A.vis(L, ["tim", "lid"], [])
    w = A.wafer(m, root)
    present(w, span(0, 0.0, 1, 0.7))
    sites = empty("s1_sites", root)
    for k, (x, z) in enumerate(A.wafer_sites()):
        if z <= A.CZ:
            A.site_kit(m, sites, x, z, f"s1s{k}")
    present(sites, span(0, 0.0, 1, 0.7))
    show(G["ub"], span(0, 0.3, 0, 0.7))
    for s in (-1, 1):
        tool(lambda mm, p, s=s: A.blade(mm, p, name=f"s1b{s}"), m, root, f"s1b{s}", span(1, 0.0, 1, 0.6),
             [(F(1, 0.0), (s * A.SITE / 2, A.RDL_Y[1] + 21.0, -300.0)), (F(1, 0.55), (s * A.SITE / 2, A.RDL_Y[1] + 21.0, 30.0))])
    lift = [(0, (0.0, 0.0, 0.0)), (F(1, 0.65), (0.0, 0.0, 0.0)), (F(1, 0.9), (0.0, 24.0, 0.0)), (F(2, 0.05), (0.0, 24.0, 0.0)),
            (F(2, 0.4), (0.0, 0.0, 0.0))]
    for n in HERO:
        A.move(L[n][1], lift)
    show(G["c4"], span(2, 0.4, 2, 0.6))
    wick(L, "uf2", F(2, 0.6), F(2, 0.95))
    tags(root, [
        [("CHIP ON WAFER", (0.0, A.DIE_Y[1], -20.0)), ("whole interposer wafer", (-150.0, A.RDL_Y[1], -120.0)), ("dies bonded face down", (-8.0, A.UB_Y[1], 0.0))],
        [("wafer cut apart", (A.SITE / 2, A.RDL_Y[1], -150.0)), ("one interposer + its dies", (0.0, A.DIE_Y[1] + 24.0, -20.0))],
        [("ON SUBSTRATE", (-40.0, A.SUB_Y[1], -50.0)), ("C4 REFLOW", (-34.0, 6.0, 0.0)), ("UNDERFILL", (20.0, 6.0, 0.0))],
    ])
    camera_path(root, [
        frame((0.0, 9.0, -60.0), 220.0, 0.30, 0.55),
        frame((0.0, 9.0, -130.0), 420.0, 0.25, 0.65, pad=1.0),
        frame((0.0, 4.0, -16.0), 130.0, 0.28, 0.28),
    ])


# ---- 2 the parts -----------------------------------------------------------------------------------


def sec2(m, root):
    pk = A.package(m, root)
    L, G = pk["L"], pk["glow"]
    A.vis(L, ALL, after(0, 0.0))
    A.flows(m, root, "s2", [0], sig=False, heat=False, n=3)
    for s in (-1, 1):
        run(root, f"s2_sig{s}", A.sig_path(s), 6, 0.35, m["g_sig"], 1, 0.1, 0.9, 40)
    A.flows(m, root, "s2h", [2], sig=False, pwr=False, n=4)
    show(G["die"], beat(2))
    tags(root, [
        [("BGA balls: to the board", (-40.0, -7.0, 0.0)), ("ABF build-up: fine copper", (-30.0, 3.0, 0.0)),
         ("glass-cloth core + PTHs", (-16.0, 0.0, 0.0)), ("C4 bumps", (-36.0, 6.0, 0.0))],
        [("silicon interposer", (-34.0, 8.0, 0.0)), ("TSVs", (-22.4, 8.5, 0.0)), ("RDL: 3 copper levels", (-30.0, 10.45, 0.0)),
         ("microbumps + underfill", (-10.0, 11.2, 0.0))],
        [("logic die, metal side down", (8.0, 13.5, 0.0)), ("HBM: base + 8 DRAM + TSVs", (26.0, 13.5, 0.0)),
         ("mold between", (17.5, 14.0, -1.0)), ("TIM + copper lid", (0.0, A.LID_Y[1], -6.0))],
    ])
    camera_path(root, [V_SUB, V_IP, V_TOP])


# ---- 3 in order -------------------------------------------------------------------------------------


def sec3(m, root):
    pk = A.package(m, root)
    L, G = pk["L"], pk["glow"]
    A.vis(L, ["ip"], after(0, 0.0))
    A.vis(L, ["ub", "die"], after(0, 0.1))
    A.vis(L, ["hbm"], after(0, 0.45))
    A.vis(L, ["uf1"], after(1, 0.05))
    A.vis(L, ["mold"], after(1, 0.3))
    A.vis(L, ["c4"], after(1, 0.65))
    A.vis(L, ["sub", "bga"], after(2, 0.0))
    A.vis(L, ["uf2"], after(2, 0.35))
    A.vis(L, ["tim"], after(2, 0.6))
    A.vis(L, ["lid"], after(2, 0.65))
    hero_up = 30.0
    rest = [(F(2, 0.0), (0.0, hero_up, 0.0)), (F(2, 0.05), (0.0, hero_up, 0.0)), (F(2, 0.3), (0.0, 0.0, 0.0))]
    for n in ("die", "ub"):
        A.move(L[n][1], [(0, (0.0, 20.0 + hero_up, 0.0)), (F(0, 0.1), (0.0, 20.0 + hero_up, 0.0)), (F(0, 0.35), (0.0, hero_up, 0.0))] + rest)
    for n in ("ip", "uf1", "c4", "hbm"):
        A.move(L[n][1], [(0, (0.0, hero_up, 0.0))] + rest)
    A.move(L["mold"][1], [(0, (0.0, hero_up + 10.0, 0.0)), (F(1, 0.3), (0.0, hero_up + 10.0, 0.0)), (F(1, 0.5), (0.0, hero_up, 0.0))] + rest)
    for k, sg in enumerate(pk["hbm"]):
        u = 0.45 + 0.1 * k
        A.move(sg, [(0, (0.0, 16.0, 0.0)), (F(0, u), (0.0, 16.0, 0.0)), (F(0, u + 0.1), (0.0, 0.0, 0.0))])
    wick(L, "uf1", F(1, 0.05), F(1, 0.3))
    show(G["c4"], span(2, 0.3, 2, 0.4))
    wick(L, "uf2", F(2, 0.35), F(2, 0.6))
    A.drop(L, "tim", 2, 0.6, 0.7, h=10.0)
    A.drop(L, "lid", 2, 0.65, 0.85, h=20.0)
    y = hero_up
    tags(root, [
        [("1 die placed face down", (0.0, A.DIE_Y[1] + y, -20.0)), ("bonded on the interposer", (-14.0, A.UB_Y[1] + y, 0.0)),
         ("HBM stacks beside it", (A.HBM_X[1], A.DIE_Y[1] + y, -8.0))],
        [("2 underfill", (-8.0, A.UB_Y[1] + y, 0.0)), ("mold", (A.DIE_X + 1.5, A.DIE_Y[1] + y, -1.0)),
         ("thinned: C4 on the TSVs", (-30.0, 6.0 + y, 0.0))],
        [("3-4 cut, onto the substrate", (-40.0, A.SUB_Y[1], -50.0)), ("underfill again", (0.0, 6.0, 0.0)), ("5 lid, test, ship", (0.0, A.LID_Y[1], -20.0))],
    ])
    camera_path(root, [
        frame((0.0, 12.0 + y, -16.0), 110.0, 0.30, 0.30),
        frame((0.0, 9.0 + y, -6.0), 110.0, 0.25, 0.20),
        frame((0.0, 8.0, -16.0), 140.0, 0.28, 0.30),
    ])


# ---- 4 yield ---------------------------------------------------------------------------------------


def sec4(m, root):
    pk = A.package(m, root)
    L, G = pk["L"], pk["glow"]
    A.vis(L, [n for n in ALL if n != "lid"], after(0, 0.0))
    A.vis(L, ["lid"], [])
    good = A.yield_marks(m, root, m["g_good_a"])
    bad = A.yield_marks(m, root, m["g_bad_a"], name="yb")
    show(good[0], span(0, 0.2, 2, 0.5))
    for k, g in enumerate(good[1:], start=1):
        show(g, span(1, 0.05 + 0.08 * k, 2, 0.5))
    culprit = bad[2]  # an HBM stack
    show(culprit, after(2, 0.15))
    for k, g in enumerate(bad):
        if k != 2:
            show(g, after(2, 0.5))
    tags(root, [
        [("one part: 99% good", (0.0, A.DIE_Y[1], 0.3)), ("logic die, tested", (-10.0, A.DIE_Y[1], -20.0))],
        [("x 10 parts and joints", (A.SUB_X, 0.0, 0.3)), ("0.99^10 = ~90%", (0.0, A.DIE_Y[1], -20.0)), ("YIELD STACKUP", (-A.SUB_X, 8.0, 0.3))],
        [("one HBM stack fails", (26.0, A.DIE_Y[1], 0.3)), ("whole package scrapped", (-30.0, 0.0, 0.3)), ("so: KNOWN-GOOD DIES only", (0.0, A.DIE_Y[1], -30.0))],
    ])
    camera_path(root, [frame((0.0, 12.0, -4.0), 70.0, 0.20, 0.20), V_FACE, V_FACE])


# ---- 5 capacity --------------------------------------------------------------------------------------


def sec5(m, root):
    R = 300.0
    big = A.wafer(m, root, R=R, cut_front=False, name="w_big")
    present(big, beat(0) + beat(1))
    sites = A.wafer_sites(R=R) + [(0.0, A.CZ)]
    marks = empty("s5_marks", root)
    for k, (x, z) in enumerate(sites):
        g = empty(f"s5_m{k}", marks)
        A.site_kit(m, g, x, z, f"s5k{k}")
        show(g, after(0, 0.05 + 0.035 * k) if k < 22 else after(0, 0.8))
    present(marks, beat(0) + beat(1))
    # beat 1: a wafer of half-size interposers beside it
    small_v = empty("w_small_v", root)
    small = empty("w_small_g", small_v)
    A.move(small, [(0, (720.0, 0.0, 0.0))])
    A.wafer(m, small, R=R, cut_front=False, name="w_small")
    k = 0
    for i in range(-7, 8):
        for j in range(-7, 8):
            x, z = i * 46.0, A.CZ + j * 46.0
            if (abs(x) + 23.0) ** 2 + (abs(z - A.CZ) + 23.0) ** 2 <= (R + 4.0) ** 2:
                bx(f"s5_sm{k}", (x - 9.0, A.UB_Y[1], z - 12.0), (x + 9.0, A.DIE_Y[1], z + 12.0), m["a_die"], small)
                k += 1
    present(small_v, beat(1))
    # beat 2: the line
    cv = A.conveyor(m, root, -300.0, 300.0, -40.0, 0.0)
    present(cv, beat(2))
    line = empty("s5_line", root)
    present(line, beat(2))
    for k in range(8):
        g = A.mini_package(m, line, 0.0, -4.0, f"s5p{k}")
        x0 = -270.0 + 64.0 * k
        A.move(g, [(F(2, 0.0), (x0, 0.0, 0.0)), (F(2, 0.99), (x0 + 64.0, 0.0, 0.0))])
    gate = empty("s5_gate", root)
    bx("s5_gate_l", (100.0, -3.0, -50.0), (110.0, 40.0, -42.0), m["a_tool"], gate)
    bx("s5_gate_r", (100.0, -3.0, 2.0), (110.0, 40.0, 10.0), m["a_tool"], gate)
    bx("s5_gate_t", (100.0, 40.0, -50.0), (110.0, 46.0, 10.0), m["a_tool"], gate)
    present(gate, beat(2))
    tags(root, [
        [("one 300 mm interposer wafer", (-200.0, A.RDL_Y[1], 150.0)), ("~15-20 big packages", (0.0, A.DIE_Y[1], -32.0))],
        [("big: ~2.5-3.3x reticle", (0.0, A.DIE_Y[1], -32.0)), ("half the size: 4x as many", (720.0, A.DIE_Y[1], -32.0))],
        [("CAPACITY: wafers a month", (105.0, 46.0, -20.0)), ("the line sets the output", (-150.0, 6.0, -4.0))],
    ])
    camera_path(root, [
        frame((0.0, 9.0, -32.0), 640.0, 0.0, 1.05, pad=1.0),
        frame((360.0, 9.0, -32.0), 1400.0, 0.0, 1.05, pad=1.0),
        frame((0.0, 10.0, -20.0), 460.0, 0.28, 0.40),
    ])


# ---- 6 OSAT -------------------------------------------------------------------------------------------


def sec6(m, root):
    pk = A.package(m, root)
    L, G = pk["L"], pk["glow"]
    A.vis(L, ALL, after(2, 0.0))
    # left: the fab's chip-on-wafer, at x = -400
    fab_v = empty("s6_fab_v", root)
    fab = empty("s6_fab", fab_v)
    A.move(fab, [(0, (-400.0, 0.0, 0.0))])
    w = A.wafer(m, fab, R=150.0, cut_front=False, name="s6w")
    for k, (x, z) in enumerate([(x, z) for (x, z) in A.wafer_sites(R=150.0)] + [(0.0, A.CZ)]):
        A.site_kit(m, fab, x, z, f"s6k{k}")
    bx("s6_floor_l", (-180.0, -4.0, -210.0), (180.0, 4.0, 150.0), m["a_dark"], fab)
    present(fab_v, beat(0) + beat(1))
    # beat 1: the stack of cut CoW parts rides across to the OSAT
    box_v = empty("s6_box_v", root)
    box = empty("s6_box", box_v)
    bx("s6_crate", (-30.0, 0.0, -50.0), (30.0, 24.0, 10.0), m["a_tray"], box)
    for k in range(3):
        bx(f"s6_c{k}", (-24.0, 24.0 + 6.0 * k, -44.0), (24.0, 28.0 + 6.0 * k, 4.0), m["a_si"], box)
    A.move(box, [(0, (-240.0, 0.0, 0.0)), (F(1, 0.1), (-240.0, 0.0, 0.0)), (F(1, 0.85), (-80.0, 0.0, 0.0))])
    present(box_v, beat(1))
    run(root, "s6_flow", [(-240.0, 50.0, -20.0), (-80.0, 50.0, -20.0)], 6, 2.0, m["g_sig"], 1, 0.05, 0.8, 60)
    osat = empty("s6_osat", root)
    bx("s6_floor_r", (-80.0, -24.0, -120.0), (90.0, -20.0, 30.0), m["a_dark"], osat)
    present(osat, after(1, 0.0))
    sk = empty("s6_sk", root)
    A.socket(m, sk)
    present(sk, after(2, 0.5))
    A.flows(m, root, "s6", [2], u0=0.55, u1=0.95, n=3)
    show(G["c4"], span(2, 0.05, 2, 0.3))
    tags(root, [
        [("TSMC: CHIP ON WAFER", (-400.0, A.DIE_Y[1], -32.0)), ("interposer wafers (TSMC, UMC)", (-520.0, A.RDL_Y[1], 60.0))],
        [("cut parts ship out", (-160.0, 40.0, -20.0)), ("to an OSAT", (-80.0, 0.0, -50.0))],
        [("ASE / Amkor: ON SUBSTRATE", (-40.0, A.SUB_Y[1], -50.0)), ("and TEST", (-A.SUB_X - 6.0, -6.0, 0.0))],
    ])
    camera_path(root, [
        frame((-400.0, 9.0, -40.0), 330.0, 0.25, 0.75, pad=1.0),
        frame((-180.0, 20.0, -20.0), 380.0, 0.20, 0.40),
        frame((0.0, 2.0, -20.0), 150.0, 0.30, 0.28),
    ])


# ---- 7 test ------------------------------------------------------------------------------------------


def probe_on(m, root, name, b, x0, x1, z0, z1, y, xs):
    tool(lambda mm, p: A.probe_card(mm, p, x0, x1, z0, z1, 0.0, pitch=5.0), m, root, name, beat(b),
         [(0, (0.0, y + 12.0, 0.0)), (F(b, 0.15), (0.0, y + 12.0, 0.0)), (F(b, 0.35), (0.0, y, 0.0))])
    for k, x in enumerate(xs):
        run(root, f"{name}_pr{k}", [(x, y + 16.0, (z0 + z1) / 2), (x, y + 6.0, (z0 + z1) / 2), (x, y, (z0 + z1) / 2)], 3, 0.6,
            m["g_probe"], b, 0.4, 0.9, 30)


def sec7(m, root):
    pk = A.package(m, root)
    L, G = pk["L"], pk["glow"]
    # beat 0: a logic die on its own wafer (wafer sort)
    dw = empty("s7_sort", root)
    bx("s7_wf", (-120.0, -2.0, -150.0), (120.0, 0.0, 0.0), m["a_wafer"], dw)
    for i, x in enumerate((-70.0, 0.0, 70.0)):
        for j, (za, zb) in enumerate(((-44.0, 0.0), (-104.0, -60.0))):
            bx(f"s7_d{i}{j}", (x - 30.0, 0.0, za), (x + 30.0, 2.0, zb), m["a_die"], dw)
    present(dw, beat(0))
    probe_on(m, root, "s7a", 0, -28.0, 28.0, -46.0, -2.0, 2.0, (-14.0, 0.0, 14.0))
    ok = empty("s7_ok", root)
    bx("s7_okb", (-30.0, 2.05, -50.0), (30.0, 2.2, 0.3), m["g_good_a"], ok)
    bad = empty("s7_bad", root)
    bx("s7_badb", (40.0, 2.05, -50.0), (100.0, 2.2, 0.3), m["g_bad_a"], bad)
    show(ok, span(0, 0.75, 1, 0.0))
    show(bad, span(0, 0.8, 1, 0.0))
    # beat 1: after chip on wafer, probe the interposer site from its top pads
    A.vis(L, HERO, beat(1))
    A.vis(L, ALL, beat(2))
    w = A.wafer(m, root)
    present(w, beat(1))
    probe_on(m, root, "s7b", 1, -A.IP_X + 2.0, -A.HBM_X[1] - 2.0, -60.0, -2.0, A.DIE_Y[1], (-40.0, -37.0))
    for s in (-1, 1):
        run(root, f"s7_sig{s}", A.sig_path(s), 5, 0.4, m["g_sig"], 1, 0.4, 0.9, 40)
    # beat 2: final test socket
    sk = empty("s7_sk", root)
    A.socket(m, sk)
    present(sk, beat(2))
    A.flows(m, root, "s7", [2], u0=0.1, u1=0.9, n=4)
    show(G["die"], span(2, 0.3, 3, 0.0))
    tags(root, [
        [("WAFER SORT: probe every die", (0.0, 20.0, -24.0)), ("pass", (0.0, 2.2, -10.0)), ("fail: never assembled", (70.0, 2.2, -10.0))],
        [("TEST after chip on wafer", (-38.0, A.DIE_Y[1] + 18.0, -30.0)), ("die-to-HBM links checked", (17.0, 10.46, 0.0))],
        [("final TEST socket", (-A.SUB_X - 6.0, -6.0, 0.0)), ("full power, at speed", (0.0, A.LID_Y[1], -20.0)), ("burn-in screens early failures", (A.SUB_X, -10.0, 0.0))],
    ])
    camera_path(root, [
        frame((0.0, 10.0, -40.0), 170.0, 0.35, 0.40),
        frame((-20.0, 18.0, -20.0), 130.0, 0.35, 0.40),
        frame((0.0, 0.0, -16.0), 150.0, 0.30, 0.25),
    ])


# ---- 8 who makes it ------------------------------------------------------------------------------------


def sec8(m, root):
    pk = A.package(m, root)
    L, G = pk["L"], pk["glow"]
    A.vis(L, ALL, after(0, 0.0))
    order = ["bga", "sub", "c4", "uf2", "ip", "ub", "uf1", "die", "hbm", "mold", "tim", "lid"]
    gaps = {"bga": 0, "sub": 0, "c4": 8, "uf2": 8, "ip": 8, "ub": 16, "uf1": 16, "die": 16, "hbm": 16, "mold": 16, "tim": 24, "lid": 32}
    for n in order:
        A.move(L[n][1], [(0, (0.0, 0.0, 0.0)), (F(0, 0.05), (0.0, 0.0, 0.0)), (F(0, 0.4), (0.0, float(gaps[n]), 0.0))])
    tags(root, [
        [("logic die: TSMC (for NVIDIA, AMD)", (-8.0, A.DIE_Y[1] + 16.0, -20.0)), ("HBM: SK hynix, Samsung, Micron", (A.HBM_X[1], A.DIE_Y[1] + 16.0, -6.0)),
         ("lid + TIM: OSAT or TSMC", (-40.0, A.LID_Y[1] + 32.0, -20.0))],
        [("CoWoS assembly: TSMC", (-30.0, A.RDL_Y[1] + 8.0, -40.0)), ("interposer wafers: TSMC, UMC", (-34.0, 8.0 + 8.0, 0.0)),
         ("bond tools: BESI, ASMPT, Hanmi (reports)", (-10.0, A.UB_Y[1] + 16.0, 0.0))],
        [("ABF substrate: Ibiden, Unimicron", (-30.0, 2.0, 0.0)), ("ABF film: Ajinomoto", (-40.0, 3.0, -40.0)),
         ("oS + test: ASE, Amkor", (A.SUB_X, -6.0, 0.0))],
    ])
    camera_path(root, [
        frame((0.0, 30.0, -20.0), 150.0, 0.30, 0.30),
        frame((-10.0, 20.0, -4.0), 120.0, 0.22, 0.18),
        frame((-10.0, 0.0, -4.0), 130.0, 0.22, 0.12),
    ])


# ---- 9 chokepoints -------------------------------------------------------------------------------------


def sec9(m, root):
    # beat 0: queue at the line
    cv = A.conveyor(m, root, -300.0, 300.0, -40.0, 0.0)
    present(cv, beat(0))
    q = empty("s9_q", root)
    present(q, beat(0))
    for k in range(9):
        g = A.mini_package(m, q, 0.0, -4.0, f"s9q{k}", s=0.28)
        x0 = -280.0 + 34.0 * k if k < 8 else 140.0
        x1 = x0 + (6.0 if k < 8 else 120.0)
        A.move(g, [(F(0, 0.0), (x0, 0.0, 0.0)), (F(0, 0.99), (x1, 0.0, 0.0))])
    gate = empty("s9_gate", root)
    bx("s9_gl", (40.0, -3.0, -50.0), (50.0, 40.0, -42.0), m["a_tool"], gate)
    bx("s9_gr", (40.0, -3.0, 2.0), (50.0, 40.0, 10.0), m["a_tool"], gate)
    bx("s9_gt", (40.0, 40.0, -50.0), (50.0, 46.0, 10.0), m["a_tool"], gate)
    present(gate, beat(0))
    # beat 1: warpage: the package's substrate cups at reflow; edge joints crack
    pk = A.package(m, root)
    L, G = pk["L"], pk["glow"]
    up = ["c4", "uf2", "ip", "ub", "uf1", "die", "hbm", "mold"]
    A.vis(L, up, beat(1) + beat(2))
    A.vis(L, ["sub", "bga"], span(1, 0.0, 1, 0.5) + beat(2))
    A.vis(L, ["tim", "lid"], beat(2))
    warp = empty("s9_warp", root)
    n = 14
    for i in range(n):
        xa = -A.SUB_X + 2 * A.SUB_X * i / n
        xb = xa + 2 * A.SUB_X / n
        xm = (xa + xb) / 2
        dy = 3.5 * (xm / A.SUB_X) ** 2
        for nm, (y0, y1), mt in (("m", (A.SUB_Y[0], A.SB_BU[0]), "a_mask"), ("b", A.SB_BU, "a_abf"), ("c", A.SB_CORE, "a_core"),
                                 ("t", A.SB_TU, "a_abf"), ("n", (A.SB_TU[1], A.SUB_Y[1]), "a_mask")):
            bx(f"s9w{i}{nm}", (xa, y0 + dy, A.SUB_Z), (xb, y1 + dy, 0.0), m[mt], warp)
    present(warp, span(1, 0.5, 2, 0.0))
    cracks = empty("s9_cracks", root)
    for s in (-1, 1):
        for k in range(3):
            x = s * (A.C4_XS[-1] - 2.8 * k)
            bx(f"s9_cr{s}{k}", (x - 1.2, A.C4_Y[0], 0.2), (x + 1.2, A.C4_Y[1], 0.5), m["g_bad_a"], cracks)
    show(cracks, span(1, 0.55, 2, 0.0))
    show(G["c4"], span(1, 0.15, 1, 0.5))
    # beat 2: a late defect in one HBM stack scraps everything
    bad = A.yield_marks(m, root, m["g_bad_a"], name="s9b")
    show(bad[2], span(2, 0.25, 3, 0.0))
    for k, g in enumerate(bad):
        if k != 2:
            show(g, span(2, 0.55, 3, 0.0))
    tags(root, [
        [("CAPACITY: one gate", (45.0, 46.0, -20.0)), ("packages wait", (-150.0, 6.0, -4.0)), ("one supplier does most CoWoS", (180.0, 6.0, -4.0))],
        [("warpage at reflow", (-40.0, A.SUB_Y[1], -40.0)), ("edge joints crack", (A.C4_XS[-1], 6.0, 0.4)), ("bigger package, more warp", (0.0, -8.0, 0.3))],
        [("defect found at final test", (26.0, A.DIE_Y[1], 0.3)), ("die, HBM, substrate: all scrapped", (-30.0, 0.0, 0.3))],
    ])
    camera_path(root, [
        frame((0.0, 10.0, -20.0), 460.0, 0.28, 0.40),
        frame((0.0, 2.0, -4.0), 125.0, 0.12, 0.10),
        frame((0.0, 4.0, -4.0), 125.0, 0.12, 0.12),
    ])


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}


def build(n):
    m, root = start(f"section_{n}", beats=BEATS, page=PAGE)
    mats(m)
    SECTIONS[n](m, root)
    finish(f"section_{n}", page=PAGE)


if __name__ == "__main__":
    build(int(sys.argv[sys.argv.index("--") + 1]))
