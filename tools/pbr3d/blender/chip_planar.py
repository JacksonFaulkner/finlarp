"""CHIP page for PLANAR: the overview (the whole chip, then the camera glides in on the planar NMOS),
five zoom-ins a-e, and ten numbered sections. The gate lies flat on the channel and controls it from
one side only; as the channel shortens the drain's field reaches the source and current leaks past
the gate, in the off state.

Run from the repo root (all scenes, or name some after `--`):
    blender -b --factory-startup --python tools/pbr3d/blender/chip_planar.py
    blender -b --factory-startup --python tools/pbr3d/blender/chip_planar.py -- zoom_a sec4

Writes assets/chip_planar.glb (overview), assets/chip_planar_zoom_<key>.glb and
assets/chip_planar_sec<N>.glb, plus a .blend next to each. One beat is 8 s.

Overview beats (the whole chip, then in on the NMOS, drawn as the detailed device of
chip_planar_detail.py at RIG_S scale in place of chip_kit's plain transistor):
  0 whole    the whole chip, the planar NMOS lit
  1 close    glide in: gate, oxide, source, drain, body, isolation
  2 on       gate high: field from the top, the inversion layer, electrons riding source to drain
  3 shrink   a short gate: the depletion regions meet, the drain pulls the barrier down
  4 leak     gate low, yet electrons ride the surface and under-gate leak paths
  5 whole    back out

Zoom-ins (3 beats each, close-ups on their own): a the leakage paths, b short channels and DIBL,
c high-k metal gate, d FD-SOI and body bias, e Dennard scaling and its end.

Sections (3 beats each, 4 for the sources): 1 the planar era, 2 the cross-section, 3 short channels,
4 strain and high-k metal gate, 5 mature nodes, 6 Dennard arithmetic, 7 FD-SOI, 8 who makes it,
9 chokepoints, 10 sources. Each is its own close-up.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_zooms import finish, start  # noqa: E402
import chip_kit as C  # noqa: E402
from chip_kit import F, box, glide_camera, label, scale_keys, show  # noqa: E402
from sand_overview import P, empty  # noqa: E402
import chip_planar_detail as PD  # noqa: E402

BEATS = 6
CX = C.NMOS_X
RIG_S = 0.42  # the overview's detailed device is drawn at this scale inside the whole chip


def span(a, b):
    """The interval from the start of beat a to the start of beat b; a and b are beats or (beat, u)."""
    a = a if isinstance(a, tuple) else (a, 0)
    b = b if isinstance(b, tuple) else (b, 0)
    return [(F(a[0], a[1]), F(b[0], b[1]))]


def rides(root, m, d, b, which, pre, **kw):
    """Beads on visible tracks along device d's paths (chip_planar_detail.paths)."""
    p = PD.paths(d)
    keys = {"on": ("p_on", "p_trk_on"), "sub": ("p_sub_leak", "p_trk_leak"), "gidl": ("p_gidl", "p_trk_leak"),
            "punch": ("p_punch", "p_trk_leak"), "tun": ("p_tun", "p_trk_leak")}
    for w_ in which:
        bead, trk = keys[w_]
        if w_ == "tun":
            for k, pts in enumerate(p["tun"]):
                PD.ride(root, m, f"{pre}_tun{k}", pts, kw.get("n_tun", 3), b, bead, trk, u0=0.05 + 0.05 * k,
                        life=45, size=13.0)
        else:
            PD.ride(root, m, f"{pre}_{w_}", p[w_], kw.get("n", 7), b, bead, trk, life=kw.get("life", 80))


# ---- overview -------------------------------------------------------------------------------
# The whole chip, then the camera glides into the NMOS, which is the detailed planar device of
# chip_planar_detail.py drawn at RIG_S scale in place of chip_kit's plain transistor (the chip's own
# tungsten plugs land on its source, drain and gate).


def wpt(x, y):
    return (CX + RIG_S * x, RIG_S * y, 0.0)


def build():
    m, root = start("planar", BEATS, page="chip")
    C.mats(m)
    PD.mats(m)
    parts = C.chip(root, m)
    show(parts["nmos"], [])
    C.overlay(root, "pick", (CX - 400, -210, -300), (CX + 400, 160, 14), m["c_lit_thin"],
              span(0, 1) + span((5, 0.3), 6))
    g = empty("rig", root)
    g.scale = (RIG_S, RIG_S, RIG_S)
    g.location = P(CX, 1.0, 0.0)
    d0 = PD.device(g, m, lg=150.0, contacts=False, ivs=span(0, 3) + span(5, 6), pre="long")
    d1 = PD.device(g, m, lg=80.0, contacts=False, ivs=span(3, 5), pre="short")
    # beat 2: gate high: field arrows, the inversion layer, electrons riding source to drain
    PD.part("chan", (-150.0, -14.0, -PD.DZ + 80.0), (150.0, 0.0, 6.0), m["p_chan"], g, span((2, 0.2), 3))
    PD.field_arrows(g, m, d0, span((2, 0.1), 3))
    rides(g, m, d0, 2, ["on"], "b2", n=10)
    # beat 3: short gate: the depletion regions reach under it; the drain's pull on the barrier
    PD.depletion(g, m, d1, 60.0, span(3, (3, 0.45)), "dep_a")
    PD.depletion(g, m, d1, 125.0, span((3, 0.45), 5), "dep_b")
    PD.arrow("dibl", (330.0, -170.0, PD.ZD), (-200.0, -170.0, PD.ZD), 8.0, m["p_punch"],
             PD.group("dibl_g", g, span((3, 0.5), 4)))
    # beat 4: gate low, current still leaks: along the surface and under the gate
    rides(g, m, d1, 4, ["sub", "punch"], "b4", n=8)
    L = lambda text, x, y, ivs, z=0.0: label(text, (x, y, z), g, ivs)  # noqa: E731
    L("planar NMOS", 0.0, d0["top"] + 20.0, span(0, 1) + span((5, 0.3), 6))
    b1 = span((1, 0.3), 2)
    L("polysilicon gate", 0.0, 200.0, b1)
    L("SiON gate oxide", -100.0, 6.0, b1)
    L("n+ source", -520.0, -100.0, b1)
    L("n+ drain", 520.0, -100.0, b1)
    L("p-type body", -300.0, -380.0, b1)
    L("isolation oxide (STI)", 820.0, -150.0, b1, 3.0)
    L("gate high: field from the top", 0.0, 200.0, span((2, 0.1), 3), PD.ZD)
    L("electrons: source to drain", -200.0, -12.0, span((2, 0.2), 3), PD.ZD)
    L("short gate", 0.0, d1["top"] - 30.0, span(3, 4))
    L("depletion regions meet", 0.0, -230.0, span((3, 0.45), 4), 8.0)
    L("drain pulls the barrier down", 250.0, -170.0, span((3, 0.5), 4), PD.ZD)
    L("gate low: should be off", 0.0, d1["top"] - 30.0, span(4, 5))
    L("leak along the surface", -150.0, -20.0, span(4, 5), PD.ZD)
    L("leak under the gate", 0.0, -250.0, span(4, 5), PD.ZD)
    glide_camera(root, [
        C.WHOLE,
        (wpt(0.0, -110.0), 1000.0, 0.30, 0.16),
        (wpt(0.0, -90.0), 860.0, 0.25, 0.14),
        (wpt(0.0, -130.0), 900.0, 0.20, 0.12),
        (wpt(0.0, -130.0), 900.0, 0.20, 0.12),
        C.WHOLE,
    ])
    finish("planar", page="chip")


# ---- zoom-ins a-e: close-ups of the detailed device on its own --------------------------------------


def zoom_a(name="planar_zoom_a"):
    """a: the leakage paths of an off transistor: subthreshold, gate tunnelling, punch-through and
    junction (GIDL) leakage, each riding its own track."""

    def body(root, m):
        d = PD.device(root, m, lg=110.0, pre="d")
        rides(root, m, d, 0, ["sub"], "a0", n=8)
        rides(root, m, d, 1, ["tun"], "a1")
        rides(root, m, d, 2, ["punch", "gidl"], "a2")
        tg(root, "gate low: off", 0.0, d["top"] - 40.0, b_(0))
        tg(root, "subthreshold: drain to source", 100.0, -22.0, b_(0), PD.ZD)
        tg(root, "thin SiON oxide", -160.0, 6.0, b_(1))
        tg(root, "electrons tunnel into the gate", 55.0, 60.0, b_(1), PD.ZD)
        tg(root, "punch-through under the gate", 0.0, -250.0, b_(2), PD.ZD)
        tg(root, "junction / GIDL into the body", 260.0, -300.0, b_(2), PD.ZD)

    pscene(name, 3, [pz(0.0, 0.0, 2700.0, 0.25, 0.16), pz(0.0, 40.0, 1200.0, 0.20, 0.12),
                     pz(0.0, -120.0, 2700.0, 0.20, 0.12)], body)


def zoom_b(name="planar_zoom_b"):
    """b: short channels: the depletion regions meet, DIBL, the 60 mV/decade floor."""

    def body(root, m):
        d = PD.device(root, m, lg=80.0, pre="d")
        PD.depletion(root, m, d, 50.0, span(0, (0, 0.45)), "dep_a")
        PD.depletion(root, m, d, 125.0, span((0, 0.45), 2), "dep_b")
        rides(root, m, d, 1, ["punch"], "b1", n=9)
        PD.arrow("dibl", (330.0, -170.0, PD.ZD), (-200.0, -170.0, PD.ZD), 8.0, m["p_punch"],
                 PD.group("dibl_g", root, b_(1)))
        rides(root, m, d, 2, ["sub"], "b2", n=8)
        leak_chart(root, m, b_(2))
        tg(root, "short gate", 0.0, d["top"] - 40.0, b_(0))
        tg(root, "depletion regions grow and meet", 0.0, -230.0, span((0, 0.45), 1), 8.0)
        tg(root, "drain voltage lowers the barrier", 250.0, -170.0, b_(1), PD.ZD)
        tg(root, "punch-through current", -150.0, -230.0, b_(1), PD.ZD)
        tg(root, "subthreshold leak", -100.0, -20.0, b_(2), PD.ZD)
        tg(root, "off-current, log scale", CHART_X + 100.0, 380.0, b_(2))
        tg(root, "x10 per 60 mV lower Vt", CHART_X + 275.0, 60.0, b_(2))

    pscene(name, 3, [pz(0.0, -40.0, 2700.0, 0.20, 0.14), pz(0.0, -60.0, 2700.0, 0.20, 0.14),
                     pz(400.0, 0.0, 4900.0, 0.0, 0.12)], body)


def zoom_c(name="planar_zoom_c"):
    """c: poly on SiON leaks; HfO2 under the poly is thicker and leaks far less; the metal gate."""

    def body(root, m):
        d0 = PD.device(root, m, lg=130.0, ivs=b_(0), pre="d0")
        rides(root, m, d0, 0, ["tun"], "c0", n_tun=4)
        d1 = PD.device(root, m, lg=130.0, diel="hk", ivs=b_(1), pre="d1")
        PD.ride(root, m, "c1_tun", PD.paths(d1)["tun"][1], 1, 1, "p_tun", "p_trk_leak", u0=0.4, u1=0.5, life=45,
                size=13.0)
        d2 = PD.device(root, m, lg=130.0, gate="metal", diel="hk", ivs=b_(2), pre="d2")
        rides(root, m, d2, 2, ["on"], "c2", n=8)
        tg(root, "polysilicon gate", 0.0, 200.0, b_(0))
        tg(root, "SiON ~1.2 nm: tunnels", -180.0, 6.0, b_(0))
        tg(root, "HfO2 on a thin IL", -180.0, 20.0, b_(1))
        tg(root, "thicker film: far fewer cross", 0.0, 120.0, b_(1), PD.ZD)
        tg(root, "metal gate: work function sets Vt", 0.0, 200.0, b_(2))
        tg(root, "electrons: source to drain", -200.0, -12.0, b_(2), PD.ZD)
        del d2

    pscene(name, 3, [pz(0.0, 110.0, 1400.0, 0.25, 0.14), pz(0.0, 110.0, 1400.0, 0.25, 0.14),
                     pz(0.0, 40.0, 2400.0, 0.30, 0.16)], body)


def zoom_d(name="planar_zoom_d"):
    """d: bulk depletion and leak paths reach deep; FD-SOI's thin film on buried oxide; body bias."""

    def body(root, m):
        d0 = PD.device(root, m, lg=110.0, gate="metal", diel="hk", ivs=b_(0), pre="d0")
        PD.depletion(root, m, d0, 140.0, b_(0), "dep0")
        rides(root, m, d0, 0, ["punch"], "d0", n=8)
        d1 = PD.device(root, m, lg=110.0, gate="metal", diel="hk", soi=True, ivs=span(1, 3), pre="d1")
        rides(root, m, d1, 1, ["on"], "d1", n=8)
        PD.part("bias", (-PD.W, PD.BOT, -PD.DZ + 40.0), (PD.W, -150.0, 8.0), m["p_bias"], root, b_(2))
        ga = PD.group("bias_arrows", root, b_(2))
        for k, x in enumerate((-400.0, 0.0, 400.0)):
            PD.arrow(f"ba{k}", (x, -440.0, PD.ZD), (x, -170.0, PD.ZD), 8.0, m["p_bias"], ga)
        tg(root, "depletion spreads deep", 330.0, -250.0, b_(0), 8.0)
        tg(root, "leak path under the channel", 0.0, -250.0, b_(0), PD.ZD)
        tg(root, "buried oxide (BOX)", -500.0, -110.0, span(1, 3))
        tg(root, "thin undoped film", 0.0, -40.0, b_(1))
        tg(root, "back bias under the BOX", 300.0, -300.0, b_(2), 8.0)
        tg(root, "acts as a second gate", -250.0, -440.0, b_(2), 8.0)

    pscene(name, 3, [DEV, pz(0.0, -60.0, 2900.0, 0.20, 0.14), pz(0.0, -100.0, 3000.0, 0.20, 0.14)], body)


def zoom_e(name="planar_zoom_e"):
    """e: one node shrinks every size by 1/k; the power arithmetic; then the leakage wall."""
    K = 0.7

    def body(root, m):
        g = shrink_group(root, "dn", span(0, 3), 1.0, K, F(1, 0.2), F(1, 0.65))
        d = PD.device(g, m, lg=260.0, pre="d")
        rides(root, m, d, 0, ["on"], "e0", n=10)
        dk = scaled(d, K)
        rides(root, m, dk, 1, ["on"], "e1", n=6)
        rides(root, m, dk, 2, ["sub", "tun"], "e2", n=8, n_tun=2)
        tg(root, "every size x 1/k, k ~1.4", 0.0, d["top"] - 40.0, b_(0))
        tg(root, "voltage x 1/k too", -560.0, 0.0, b_(0))
        tg(root, "same design, 0.7x smaller", 0.0, K * d["top"], span((1, 0.2), 2))
        tg(root, "~2x transistors, same power", K * 400.0, -K * 250.0, span((1, 0.65), 2))
        tg(root, "Vt stuck: leaks when off", 0.0, -22.0, b_(2), PD.ZD)
        tg(root, "Vdd stalls near 1 V", 0.0, K * d["top"], b_(2))

    pscene(name, 3, [DEV, pz(0.0, 0.0, 2700.0), pz(0.0, 0.0, 2500.0)], body)


# ---- sections 1-10: a detailed planar transistor close-up (chip_planar_detail.py) -----------------
# Each section is its own cut-away device (or wafer), framed to fill the left pane; the whole chip
# is the overview's job.



def pscene(name, beats, poses, body):
    m, root = start(name, beats, page="chip")
    C.mats(m)
    PD.mats(m)
    body(root, m)
    glide_camera(root, poses)
    finish(name, page="chip")


def pz(x, y, d, yaw=0.32, pitch=0.22):
    return ((x, y, 0.0), d, yaw, pitch)


def tg(root, text, x, y, ivs, z=0.0):
    label(text, (x, y, z), root, ivs)


def b_(i):
    return span(i, i + 1)


DEV = pz(0.0, 40.0, 3000.0)  # one device, three-quarter view


def shrink_group(root, name, ivs, s0, s1, f0, f1):
    """A switched group holding a scaled group (show and scale keys on different empties)."""
    outer = PD.group(name, root, ivs)
    inner = empty(name + "_k", outer)
    scale_keys(inner, [(f0, s0), (f1, s1)])
    return inner


def scaled(d, k):
    return {key: (v * k if isinstance(v, float) else v) for key, v in d.items()}


def sec1():
    """1: Dennard shrink, the leakage wall, then the patched planar device (strain, HKMG) that
    ran to 28/22 nm."""

    def body(root, m):
        g0 = shrink_group(root, "era0", b_(0), 1.0, 0.7, F(0, 0.40), F(0, 0.75))
        d0 = PD.device(g0, m, lg=280.0, pre="d0")
        PD.on_current(root, m, d0, 0, u1=0.30)
        PD.on_current(root, m, scaled(d0, 0.7), 0, name="on_k", n=6, u0=0.78, u1=0.9)
        d1 = PD.device(root, m, lg=110.0, ivs=b_(1), pre="d1")
        PD.leak_sub(root, m, d1, 1, n=8)
        PD.leak_tunnel(root, m, d1, 1)
        d2 = PD.device(root, m, lg=110.0, gate="metal", diel="hk", liner=True, ivs=b_(2), pre="d2")
        tg(root, "polysilicon gate", 0.0, 200.0, span(0, (0, 0.4)))
        tg(root, "n+ source", -560.0, -80.0, span(0, (0, 0.4)))
        tg(root, "n+ drain", 560.0, -80.0, span(0, (0, 0.4)))
        tg(root, "every size x ~0.7 per node", 0.0, 0.7 * d0["top"], span((0, 0.4), 1))
        tg(root, "supply voltage scaled too", 0.0, 0.7 * (d0["top"] + 240.0), span((0, 0.75), 1))
        tg(root, "gate off, yet current leaks", 0.0, -16.0, b_(1), PD.ZD)
        tg(root, "thin oxide: tunnelling", -60.0, 6.0, b_(1))
        tg(root, "~2005: Vdd stalls near 1 V", 0.0, d1["top"] + 20.0, b_(1))
        tg(root, "strain liner (90 nm)", 380.0, d2["sd_top"] + 26.0, b_(2), 5.0)
        tg(root, "HfO2 + metal gate (45 nm)", -60.0, 20.0, b_(2))
        tg(root, "gate on top only: ends ~22 nm", 0.0, d2["top"] - 40.0, b_(2))

    pscene("planar_sec1", 3, [DEV, pz(0.0, 40.0, 3100.0, 0.25, 0.18), DEV], body)


def sec2():
    """2: the cross-section conducting, the gate's reach from the top only, the four leak paths."""

    def body(root, m):
        d = PD.device(root, m, lg=150.0, pre="d")
        PD.part("chan", (-150.0, -14.0, -PD.DZ + 80.0), (150.0, 0.0, 6.0), m["p_chan"], root, b_(0))
        PD.field_arrows(root, m, d, b_(0))
        PD.on_current(root, m, d, 0)
        PD.part("reach", (-260.0, -340.0, -PD.DZ + 80.0), (260.0, -70.0, 8.0), m["p_reach"], root, b_(1))
        PD.field_arrows(root, m, d, b_(1), pre="fld1", depth=-40.0)
        PD.arrow("drainfield", (300.0, -200.0, PD.ZD), (-200.0, -200.0, PD.ZD), 7.0, m["p_punch"],
                 PD.group("df", root, b_(1)))
        PD.leak_sub(root, m, d, 2)
        PD.leak_tunnel(root, m, d, 2, n=2)
        PD.leak_gidl(root, m, d, 2)
        PD.leak_punch(root, m, d, 2)
        tg(root, "poly gate", 0.0, 230.0, b_(0))
        tg(root, "SiON gate oxide", -100.0, 6.0, b_(0))
        tg(root, "n+ source", -520.0, -100.0, b_(0))
        tg(root, "n+ drain", 520.0, -100.0, b_(0))
        tg(root, "p-type body", -300.0, -380.0, b_(0))
        tg(root, "inversion layer", 0.0, -12.0, b_(0), PD.ZD)
        tg(root, "gate field: surface only", 0.0, 100.0, b_(1), PD.ZD)
        tg(root, "out of the gate's reach", 0.0, -300.0, b_(1), 8.0)
        tg(root, "drain field leaks to source", 150.0, -200.0, b_(1), PD.ZD)
        tg(root, "1 subthreshold", 140.0, -16.0, b_(2), PD.ZD)
        tg(root, "2 gate tunnelling", -75.0, 60.0, b_(2), PD.ZD)
        tg(root, "3 junction / GIDL", 240.0, -300.0, b_(2), PD.ZD)
        tg(root, "4 punch-through", 0.0, -210.0, b_(2), PD.ZD)

    pscene("planar_sec2", 3, [DEV, pz(0.0, -40.0, 2900.0, 0.15, 0.12), pz(0.0, -40.0, 2900.0, 0.15, 0.12)], body)


CHART_X = 1150.0


def leak_chart(root, m, ivs):
    """Off-current bars on a log scale, one decade per 60 mV of threshold lost."""
    g = PD.group("chart", root, ivs)
    box("chart_board", (CHART_X - 60.0, -420.0, -60.0), (CHART_X + 560.0, 420.0, -40.0), m["p_silicide"], g)
    for k in range(3):
        x = CHART_X + 40.0 + 180.0 * k
        box(f"bar{k}", (x, -380.0, -40.0), (x + 110.0, -380.0 + 220.0 * (k + 1), 0.0), m["p_sub_leak"], g)
    return g


def sec3():
    """3: long channel, short channel with DIBL, the 60 mV/decade floor."""

    def body(root, m):
        d0 = PD.device(root, m, lg=260.0, ivs=b_(0), pre="d0")
        PD.depletion(root, m, d0, 60.0, b_(0), "dep0")
        d1 = PD.device(root, m, lg=90.0, ivs=span(1, 3), pre="d1")
        PD.depletion(root, m, d1, 120.0, span(1, 3), "dep1")
        PD.leak_punch(root, m, d1, 1, depth=-170.0)
        PD.leak_sub(root, m, d1, 2, n=8)
        leak_chart(root, m, b_(2))
        tg(root, "long gate", 0.0, d0["top"] - 40.0, b_(0))
        tg(root, "depletion round each junction", 290.0, -120.0, b_(0), 8.0)
        tg(root, "barrier held by the gate", 0.0, -40.0, b_(0), PD.ZD)
        tg(root, "short gate", 0.0, d1["top"] - 40.0, b_(1))
        tg(root, "depletion regions meet", 0.0, -230.0, b_(1), 8.0)
        tg(root, "DIBL: drain lowers barrier", 200.0, -150.0, b_(1), PD.ZD)
        tg(root, "off-current, log scale", CHART_X + 100.0, 380.0, b_(2))
        tg(root, "x10 per 60 mV lower Vt", CHART_X + 275.0, 60.0, b_(2))
        tg(root, "subthreshold leak", -100.0, -16.0, b_(2), PD.ZD)

    pscene("planar_sec3", 3, [DEV, pz(0.0, -40.0, 2900.0, 0.20, 0.14), pz(400.0, 0.0, 4900.0, 0.0, 0.12)], body)


def push_arrows(root, m, ivs, mk, inward, pre, y=-30.0):
    g = PD.group(pre, root, ivs)
    for s in (-1, 1):
        a, b = s * 480.0, s * 170.0
        if not inward:
            a, b = s * 170.0, s * 480.0
        PD.arrow(f"{pre}{s}", (a, y, PD.ZD), (b, y, PD.ZD), 9.0, m[mk], g)
    return g


def sec4():
    """4: SiGe squeezes the PMOS channel, a nitride liner stretches the NMOS, then HfO2 and a metal
    gate replace SiON and poly."""

    def body(root, m):
        dp = PD.device(root, m, lg=110.0, kind="p", sige=True, ivs=b_(0), pre="dp")
        push_arrows(root, m, b_(0), "p_push", True, "push")
        dn = PD.device(root, m, lg=110.0, liner=True, ivs=b_(1), pre="dn")
        push_arrows(root, m, b_(1), "p_pull", False, "pull")
        d_old = PD.device(root, m, lg=110.0, ivs=span(2, (2, 0.45)), pre="dold")
        PD.leak_tunnel(root, m, d_old, 2, n=3, u1=0.2)
        d_new = PD.device(root, m, lg=110.0, gate="metal", diel="hk", ivs=span((2, 0.45), 3), pre="dnew")
        tg(root, "SiGe source/drain (PMOS)", -560.0, 20.0, b_(0))
        tg(root, "channel squeezed: holes faster", 0.0, -30.0, b_(0), PD.ZD)
        tg(root, "n-well", -300.0, -380.0, b_(0))
        tg(root, "nitride liner pulls (NMOS)", 420.0, dn["sd_top"] + 26.0, b_(1), 5.0)
        tg(root, "channel stretched", 0.0, -30.0, b_(1), PD.ZD)
        tg(root, "poly on thin SiON: leaks", 0.0, 6.0, span(2, (2, 0.45)))
        tg(root, "HfO2 on a thin IL", -60.0, 20.0, span((2, 0.45), 3))
        tg(root, "metal gate sets Vt", 0.0, d_new["top"] - 60.0, span((2, 0.45), 3))
        del dp

    pscene("planar_sec4", 3, [DEV, DEV, pz(0.0, 40.0, 2500.0, 0.30, 0.18)], body)


def sec5():
    """5: mature nodes and who ships them: bulk planar at 28 nm and up, FD-SOI, SMIC."""

    def body(root, m):
        d0 = PD.device(root, m, lg=110.0, gate="metal", diel="hk", ivs=b_(0), pre="d0")
        d1 = PD.device(root, m, lg=110.0, gate="metal", diel="hk", soi=True, ivs=b_(1), pre="d1")
        d2 = PD.device(root, m, lg=150.0, ivs=b_(2), pre="d2")
        PD.on_current(root, m, d0, 0)
        PD.on_current(root, m, d1, 1)
        PD.on_current(root, m, d2, 2)
        tg(root, "bulk planar, 28 nm class", 0.0, d0["top"] - 40.0, b_(0))
        tg(root, "28 nm+: 36% of foundry revenue", -520.0, -200.0, b_(0))
        tg(root, "down from 54% in 2021", 520.0, -200.0, b_(0))
        tg(root, "GF 22FDX: FD-SOI", 0.0, d1["top"] - 40.0, b_(1))
        tg(root, "buried oxide", -500.0, -110.0, b_(1))
        tg(root, "UMC: 22/28 nm ~35-40% of sales", 520.0, -300.0, b_(1))
        tg(root, "SMIC: mostly 28 nm and above", 0.0, d2["top"] - 40.0, b_(2))
        tg(root, "MCUs, power, display, RF", 520.0, -200.0, b_(2))

    pscene("planar_sec5", 3, [DEV, DEV, DEV], body)


def sec6():
    """6: Dennard arithmetic: shrink by 1/k, power per gate falls by 1/k^2, then the leakage wall."""
    K = 0.7

    def body(root, m):
        g = shrink_group(root, "dn", span(0, 3), 1.0, K, F(1, 0.25), F(1, 0.70))
        d = PD.device(g, m, lg=260.0, pre="d")
        PD.on_current(root, m, d, 0)
        PD.on_current(root, m, scaled(d, K), 1, name="on_k", n=6, u0=0.72, u1=0.95)
        dk = scaled(d, K)
        PD.leak_sub(root, m, dk, 2, n=8)
        PD.leak_tunnel(root, m, dk, 2, n=2)
        tg(root, "gate length L", 0.0, d["top"] - 40.0, b_(0))
        tg(root, "oxide t_ox", -120.0, 6.0, b_(0))
        tg(root, "L, W, t_ox, Vdd all x 1/k", 560.0, -100.0, b_(0))
        tg(root, "k ~1.4: x0.7 per node", 0.0, K * d["top"], span((1, 0.25), 2))
        tg(root, "power per gate x 1/k^2", -K * 120.0, K * 120.0, span((1, 0.7), 2))
        tg(root, "gates per area x k^2", K * 560.0, -200.0, span((1, 0.7), 2))
        tg(root, "Ioff x10 per 60 mV of Vt", 0.0, -16.0, b_(2), PD.ZD)
        tg(root, "Vdd stuck near 1 V", 0.0, K * d["top"], b_(2))

    pscene("planar_sec6", 3, [DEV, pz(0.0, 0.0, 2700.0), pz(0.0, 0.0, 2500.0)], body)


def sec7():
    """7: bulk depletion and leak paths reach deep; FD-SOI's film on BOX; body bias under it."""

    def body(root, m):
        d0 = PD.device(root, m, lg=110.0, gate="metal", diel="hk", ivs=b_(0), pre="d0")
        PD.depletion(root, m, d0, 140.0, b_(0), "dep0")
        PD.leak_punch(root, m, d0, 0, depth=-260.0)
        d1 = PD.device(root, m, lg=110.0, gate="metal", diel="hk", soi=True, ivs=span(1, 3), pre="d1")
        PD.leak_sub(root, m, d1, 1, n=3)
        PD.part("bias", (-PD.W, PD.BOT, -PD.DZ + 40.0), (PD.W, -150.0, 8.0), m["p_bias"], root, b_(2))
        ga = PD.group("bias_arrows", root, b_(2))
        for k, x in enumerate((-400.0, 0.0, 400.0)):
            PD.arrow(f"ba{k}", (x, -440.0, PD.ZD), (x, -170.0, PD.ZD), 8.0, m["p_bias"], ga)
        tg(root, "bulk: depletion spreads deep", 330.0, -250.0, b_(0), 8.0)
        tg(root, "leak path under the channel", 0.0, -260.0, b_(0), PD.ZD)
        tg(root, "random dopants vary Vt", -400.0, -380.0, b_(0))
        tg(root, "buried oxide (BOX)", -500.0, -110.0, span(1, 3))
        tg(root, "film a few nm, undoped", 0.0, -40.0, b_(1))
        tg(root, "no path below the channel", 300.0, -110.0, b_(1))
        tg(root, "back bias under the BOX", 300.0, -300.0, b_(2), 8.0)
        tg(root, "forward: faster; reverse: less leak", -250.0, -440.0, b_(2), 8.0)

    pscene("planar_sec7", 3, [DEV, pz(0.0, -60.0, 2900.0, 0.20, 0.14), pz(0.0, -100.0, 3000.0, 0.20, 0.14)], body)


def sec8():
    """8: who makes it: TSMC's 28 nm planar, Intel's 22 nm fin ending planar at the top, Soitec's
    SOI wafers."""

    def body(root, m):
        d = PD.device(root, m, lg=110.0, gate="metal", diel="hk", ivs=span(0, 2), pre="d")
        PD.on_current(root, m, d, 0)
        PD.part("gate_hl", (-110.0, 0.0, -PD.DZ + 60.0), (110.0, d["top"], 10.0), m["p_hl"], root, b_(1))
        PD.part("body_hl", (-260.0, -320.0, -PD.DZ + 80.0), (260.0, -60.0, 8.0), m["p_reach"], root, b_(1))
        PD.soi_wafer(root, m, b_(2))
        tg(root, "TSMC: 28 nm, still a big line", 0.0, d["top"] - 40.0, b_(0))
        tg(root, "HKMG planar transistor", -80.0, 20.0, b_(0))
        tg(root, "Intel: FinFET at 22 nm (2011)", 0.0, d["top"] - 40.0, b_(1))
        tg(root, "planar: gate on top only", 0.0, -200.0, b_(1), 8.0)
        tg(root, "Soitec: SOI wafers", 0.0, 120.0, b_(2), -200.0)
        tg(root, "top silicon film", -250.0, 54.0, b_(2), 4.0)
        tg(root, "buried oxide", -250.0, 15.0, b_(2), 2.0)
        tg(root, "handle wafer", -250.0, -70.0, b_(2))

    pscene("planar_sec8", 3, [DEV, DEV, pz(0.0, 0.0, 2800.0, 0.20, 0.40)], body)


def sec9():
    """9: mature-node overcapacity, FD-SOI's niche, node names that are not gate lengths."""

    def body(root, m):
        n = 8
        each = [span((0, 0.05 + 0.08 * k), 1) for k in range(n)]
        PD.wafer_stack(root, m, n, each, c=(0.0, -200.0, -300.0))
        d1 = PD.device(root, m, lg=110.0, gate="metal", diel="hk", soi=True, ivs=b_(1), pre="d1")
        PD.on_current(root, m, d1, 1)
        d2 = PD.device(root, m, lg=110.0, gate="metal", diel="hk", ivs=b_(2), pre="d2")
        PD.part("lg_bar", (-110.0, d2["top"] + 30.0, -10.0), (110.0, d2["top"] + 44.0, 10.0), m["p_bar"], root, b_(2))
        tg(root, "UMC 2025: wafers shipped +12.3%", 0.0, -200.0 + 46.0 * 7 + 15.0, span((0, 0.6), 1), -300.0)
        tg(root, "but revenue only +2.3%", 0.0, -200.0, b_(0), 220.0)
        tg(root, "FD-SOI: IoT, RF, automotive", 0.0, d1["top"] - 40.0, b_(1))
        tg(root, "buried oxide", -500.0, -110.0, b_(1))
        tg(root, "real gate length", 0.0, d2["top"] + 44.0, b_(2), 10.0)
        tg(root, "'28 nm' is a name, not a ruler", 520.0, -200.0, b_(2))

    pscene("planar_sec9", 3, [pz(0.0, -20.0, 2300.0, 0.15, 0.40), DEV, pz(0.0, 120.0, 2600.0, 0.25, 0.20)], body)


def sec10():
    """10: sources, one beat per group of cards, each on the part of the device it backs."""

    def body(root, m):
        d0 = PD.device(root, m, lg=90.0, ivs=b_(0), pre="d0")
        PD.depletion(root, m, d0, 120.0, b_(0), "dep0")
        PD.leak_punch(root, m, d0, 0, depth=-170.0)
        d1 = PD.device(root, m, lg=110.0, gate="metal", diel="hk", soi=True, ivs=b_(1), pre="d1")
        d2 = PD.device(root, m, lg=110.0, kind="p", sige=True, ivs=b_(2), pre="d2")
        push_arrows(root, m, b_(2), "p_push", True, "push")
        each = [span((3, 0.05 + 0.08 * k), 4) for k in range(6)]
        PD.wafer_stack(root, m, 6, each, c=(0.0, -200.0, -300.0))
        tg(root, "[1] Dennard's end; short channels", 0.0, -230.0, b_(0), 8.0)
        tg(root, "[2] FD-SOI: Soitec, Compound Semi", -500.0, -110.0, b_(1))
        tg(root, "[3] strain: Intel 90 nm, EDN", 0.0, -30.0, b_(2), PD.ZD)
        tg(root, "[4] Counterpoint: mature share", 0.0, -200.0 + 46.0 * 5 + 15.0, span((3, 0.55), 4), -300.0)
        tg(root, "[5] UMC 2025 results (SEC)", 0.0, -200.0, b_(3), 220.0)
        tg(root, "[6] node naming: PC Gamer, EE Journal", -380.0, -200.0 + 46.0 * 5 + 15.0, span((3, 0.55), 4), -300.0)
        del d1, d2

    pscene("planar_sec10", 4, [DEV, DEV, DEV, pz(0.0, -40.0, 2300.0, 0.15, 0.40)], body)


SCENES = {
    "zoom_a": zoom_a, "zoom_b": zoom_b, "zoom_c": zoom_c, "zoom_d": zoom_d, "zoom_e": zoom_e,
    "sec1": sec1, "sec2": sec2, "sec3": sec3, "sec4": sec4, "sec5": sec5,
    "sec6": sec6, "sec7": sec7, "sec8": sec8, "sec9": sec9, "sec10": sec10,
}


if __name__ == "__main__":
    wanted = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for name in wanted or ["overview"] + list(SCENES):
        if name == "overview":
            build()
        else:
            SCENES[name]()
