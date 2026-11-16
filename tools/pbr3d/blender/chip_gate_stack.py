"""CHIP pictures for the GATE STACK node: the overview, zoom-ins a-e and sections 1-10.

Run from the repo root (all of them, or name some after `--`):

    blender -b --factory-startup --python tools/pbr3d/blender/chip_gate_stack.py
    blender -b --factory-startup --python tools/pbr3d/blender/chip_gate_stack.py -- zoom_a sec4

Writes blender/chip_gate_stack[_zoom_<key>|_sec<N>].blend and assets/chip_gate_stack[...].glb.
One beat is 8 s.

The overview (beats 0-5): the whole chip, then in on the NMOS, drawn as the detailed
replacement-gate rig of chip_gate_stack_detail.py at RIG_S scale in place of chip_kit's plain gate.

  zoom a  the layers, from interlayer to fill, on a stepped cut-away (4 beats)
  zoom b  gate-last: dummy poly, S/D anneal and ILD, poly pull, the stack goes in (4 beats)
  zoom c  EOT: thin SiO2 leaks, HfO2 thick at the same EOT, Intel 45 nm, the formula (4 beats)
  zoom d  work-function metals: NMOS TiAlC(N), PMOS TiN, a La dipole, both gates (4 beats)
  zoom e  a nanosheet stack: wrapped sheets, what fits, Vt varies, current in the sheets (4 beats)
  sec 1-10 one close-up rig each, following the page's headings (see each function)

Every zoom and section is its own close-up rig, not the whole chip. Films are drawn far thicker
than life next to the gate width.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chip_kit as C  # noqa: E402
from sand_overview import F, P, empty, label, mat, show  # noqa: E402
from sand_zooms import finish, start  # noqa: E402
from chip_kit import overlay  # noqa: E402

BEATS = 6
NAME = "gate_stack"
CX = C.NMOS_X  # the gate is centred on the NMOS

RIG_S = 0.4  # the overview's detailed rig is drawn at this scale inside the whole chip


def mats(m):
    m["glow"] = mat("chip_gate_stack_glow", (1.0, 0.72, 0.35), emit=(1.0, 0.65, 0.25), strength=1.0, alpha=0.22)
    m["hl"] = mat("chip_gate_stack_hl", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=1.0, alpha=0.16)


def during(a, b):
    """On from the start of beat a to the start of beat b."""
    return [(F(a, 0), F(b, 0))]


def tag(root, text, x, y, ivs):
    label(text, (x, y, 0.0), root, ivs)


def name_of(stem):
    return f"{NAME}_{stem}"


# ---- the overview -------------------------------------------------------------------------
# The whole chip, then the camera glides into the NMOS, which is the detailed replacement-gate
# rig (chip_gate_stack_detail.py) drawn at RIG_S scale in place of chip_kit's plain gate.


def w(x, y):
    """Rig coordinates to chip coordinates (for camera targets)."""
    return (CX + RIG_S * x, RIG_S * y, 0.0)


def build(name=NAME):
    m, root = start(name, BEATS, page="chip")
    C.mats(m)
    mats(m)
    D.mats(m)
    parts = C.chip(root, m)
    show(parts["nmos"], [])  # the detailed rig below stands in for it
    overlay(root, "nmos_hl", (CX - 330, -150, -250), (CX + 330, 180, 14), m["hl"],
            [(F(0, 0), F(1, 0.2)), (F(5, 0.4), F(6, 0))])
    g = empty("rig", root)
    g.scale = (RIG_S, RIG_S, RIG_S)
    g.location = P(CX, 1.0, 0.0)
    D.frame(g, m)
    w_ = D.trench(g, m)
    # beats 2-4: the gate is high; its field runs down through the films into the silicon
    D.part("gate_glow", (-222.0, 0.0, -D.DZ), (222.0, D.H + 4.0, 6.0), m["glow"], g, sp((2, 0.1), 5))
    fld = D.group("field", g, sp((2, 0.15), 4))
    for k, x in enumerate((-120.0, 0.0, 120.0)):
        D.arrow(f"fld{k}", (x, 330.0, 24.0), (x, -40.0, 24.0), 5.0, m["d_field"], fld)
    # beat 3: electrons pulled up from the body gather in the inversion layer
    for k, x in enumerate((-150.0, -50.0, 50.0, 150.0)):
        D.path_run(g, m, f"inv{k}", D.arc((x, -300.0, 24.0), (x, -8.0, 24.0), 0.0, 4), 3, 3, 0.05 + 0.05 * k,
                   0.6, 50, ivs=sp(3, 4), size=10.0)
    D.part("inversion", (-220.0, -14.0, -D.DZ + 40.0), (220.0, 0.0, 8.0), m["d_chan"], g, sp((3, 0.4), 5))
    # beat 4: rulers beside the floor films: physical thickness (cyan), EOT (pink)
    phys = w_["hk"][2] + 26.0  # top of the HfO2 on the floor
    D.part("r_phys", (-330.0, 0.0, 10.0), (-304.0, phys, 30.0), m["d_phys"], g, sp(4, 5))
    D.part("r_eot", (-294.0, 0.0, 10.0), (-268.0, phys * 0.85 / 2.3, 30.0), m["d_eot"], g, sp(4, 5))
    L = lambda text, x, y, ivs, z=0.0: label(text, (x, y, z), g, ivs)  # noqa: E731
    whole = [(F(0, 0), F(1, 0.2)), (F(5, 0.4), F(6, 0))]
    L("NMOS gate stack", 0.0, 560.0, whole)
    b1 = sp((1, 0.3), 2)
    L("IL SiOx ~0.5 nm", -120.0, 6.0, b1)
    L("HfO2 high-k ~1.8 nm", -207.0, 250.0, b1)
    L("TiAlC(N) work-function", w_["wfm"][0] + 12.0, 160.0, b1)
    L("W fill: gate metal", 0.0, 300.0, b1)
    L("gate high: field runs down", 120.0, 250.0, sp((2, 0.15), 3), 24.0)
    L("no current crosses the HfO2", -207.0, 120.0, sp((2, 0.15), 3))
    L("electrons pulled up", -150.0, -200.0, sp(3, 4), 24.0)
    L("inversion layer: channel on", 150.0, -7.0, sp((3, 0.4), 4), 8.0)
    L("physical ~2.3 nm", -317.0, phys, sp(4, 5), 30.0)
    L("EOT ~0.85 nm: acts thinner", -281.0, phys * 0.85 / 2.3, sp(4, 5), 30.0)
    L("HfO2 + IL on the floor", -120.0, 20.0, sp(4, 5))
    L("tungsten contacts", 475.0, 330.0, sp((2, 0.15), 3), -150.0)
    C.glide_camera(root, [
        C.WHOLE,
        (w(-60.0, 120.0), 520.0, 0.35, 0.18),
        (w(0.0, 60.0), 900.0, 0.30, 0.16),
        (w(0.0, -80.0), 900.0, 0.25, 0.14),
        (w(-240.0, 30.0), 300.0, 0.25, 0.14),
        C.WHOLE,
    ])
    finish(name, page="chip")


# ---- zoom-ins a-e: close-up rigs on their own ----------------------------------------------------


def zoom_a(stem="zoom_a"):
    """The layers, from interlayer to fill, on a stepped cut-away of one replacement gate."""

    def body(root, m):
        _, p = stair_rig(root, m)
        ztag(root, "IL SiOx ~0.5 nm", (-40.0, p["il"][1], p["il"][2]), during(0, 1))
        ztag(root, "HfO2 high-k ~1.8 nm", (-40.0, p["hk"][1], p["hk"][2]), during(0, 1))
        ztag(root, "silicon channel", (0.0, -40.0, 0.0), during(0, 1))
        ztag(root, "TiN cap", (p["cap"][0], 160.0, p["cap"][2]), during(1, 2))
        ztag(root, "TiAlC(N): sets NMOS Vt", (p["wfm"][0], 260.0, p["wfm"][2]), during(1, 2))
        ztag(root, "TiN barrier", (p["bar"][0], 330.0, p["bar"][2]), during(2, 3))
        ztag(root, "W fill: low resistance", (0.0, 260.0, p["fill"][2]), during(2, 3))
        ztag(root, "four films in a U", (-p["hk"][0], 360.0, p["hk"][2]), during(3, 4))
        ztag(root, "nitride spacer", (-242.0, 330.0, 0.0), during(3, 4))

    dscene(name_of(stem), 4, [pose(-100.0, 50.0, 600.0, 0.45, 0.30), pose(-110.0, 200.0, 850.0, 0.45, 0.26),
                              pose(-40.0, 240.0, 1000.0, 0.40, 0.24), pose(60.0, 40.0, 2000.0, 0.35, 0.22)], body)


def zoom_b(stem="zoom_b"):
    """Gate-last: dummy poly, the S/D anneal and ILD fill, poly pull, the stack goes in."""

    def body(root, m):
        D.frame(root, m, ild=sp((1, 0.55), 4), sd=sp((1, 0.05), 4))
        D.dummy(root, m, ivs=sp(0, (2, 0.35)))
        D.anneal(root, m, ivs=sp((1, 0.15), (1, 0.5)))
        D.part("pull_glow", (-220.0, 0.0, -D.DZ), (220.0, D.H, 6.0), m["d_hl"], root, sp((2, 0.35), (2, 0.7)))
        # etchant dots carrying the poly away
        for k, x in enumerate((-120.0, 0.0, 120.0)):
            D.path_run(root, m, f"etch{k}", D.arc((x, 200.0, 20.0), (x, 600.0, 20.0), 0.0, 3), 3, 2, 0.30, 0.65,
                       40, "d_ald", "d_trk_e", 10.0, ivs=sp((2, 0.3), (2, 0.75)))
        on = {k: sp((3, 0.05 + 0.1 * i), 4) for i, k in enumerate(("il", "hk", "cap", "wfm", "bar", "fill"))}
        D.trench(root, m, on=on)
        tag(root, "dummy polysilicon gate", 0.0, 260.0, during(0, 1))
        tag(root, "nitride spacers", 242.0, 330.0, during(0, 1))
        tag(root, "n+ source/drain epi", -420.0, 0.0, sp((1, 0.05), 2))
        tag(root, "anneal ~1000 C", 420.0, -120.0, sp((1, 0.15), (1, 0.5)))
        tag(root, "ILD0 oxide, polished", 450.0, 260.0, sp((1, 0.55), 2))
        tag(root, "poly etched out", 0.0, 400.0, sp((2, 0.3), (2, 0.7)))
        tag(root, "etch products pumped away", 120.0, 560.0, sp((2, 0.3), (2, 0.75)))
        tag(root, "empty trench", 0.0, 200.0, sp((2, 0.7), 3))
        tag(root, "IL, HfO2, metals line it", -205.0, 150.0, sp((3, 0.15), 4))
        tag(root, "W fill, polished flat", 0.0, 300.0, sp((3, 0.55), 4))

    dscene(name_of(stem), 4, [pose(60.0, 120.0, 1700.0, 0.30, 0.22), pose(60.0, 20.0, 2200.0, 0.30, 0.22),
                              pose(30.0, 160.0, 1900.0, 0.30, 0.22), pose(-30.0, 170.0, 1300.0, 0.30, 0.22)], body)


def zoom_c(stem="zoom_c"):
    """EOT: thin SiO2 leaks; HfO2 thick at the same EOT; Intel 45 nm, over 10x less leakage; EOT."""

    def body(root, m):
        yl, yr = eot_columns(root, m)
        for b, n in ((0, 3), (2, 3)):
            for k, x in enumerate((-400.0, -300.0, -200.0)):
                D.path_run(root, m, f"lk{b}_{k}", [(x, -60.0, 14.0), (x, yl["gate"] + 60.0, 14.0)], n, b,
                           0.04 + 0.05 * k, 0.85, 45, "d_elec", "d_trk_e", 10.0)
        D.path_run(root, m, "rk2", [(300.0, -60.0, 14.0), (300.0, yr["gate"] + 60.0, 14.0)], 1, 2, 0.4, 0.5, 45,
                   "d_elec", "d_trk_e", 10.0)
        for cx, phys, eot in ((-300.0, 1.2, 1.2), (300.0, 2.3, 0.85)):
            x = cx + D.EOT_HW + 24.0
            D.part(f"phys{cx:.0f}", (x, 0.0, -20.0), (x + 22.0, phys * D.NM, 10.0), m["d_phys"], root, sp(1, 2))
            D.part(f"eot{cx:.0f}", (x + 34.0, 0.0, -20.0), (x + 56.0, eot * D.NM, 10.0), m["d_eot"], root, sp(1, 2))
        D.part("il_hl", (300.0 - D.EOT_HW - 4, -2.0, -40.0), (300.0 + D.EOT_HW + 4, 22.0, 10.0), m["d_hl"], root,
               sp(3, 4))
        D.part("hk_hl", (300.0 - D.EOT_HW - 4, 20.0, -40.0), (300.0 + D.EOT_HW + 4, 94.0, 10.0), m["glow"], root,
               sp(3, 4))
        tag(root, "SiO2 1.2 nm", -440.0, 24.0, during(0, 1))
        tag(root, "electrons tunnel through", -300.0, 200.0, during(0, 1))
        tag(root, "physical 2.3 nm", 300.0 + D.EOT_HW + 35.0, 92.0, during(1, 2))
        tag(root, "EOT ~0.85 nm", 300.0 + D.EOT_HW + 69.0, 34.0, during(1, 2))
        tag(root, "SiO2: many leak", -300.0, 200.0, during(2, 3))
        tag(root, "HKMG: >10x less (Intel)", 300.0, 200.0, during(2, 3))
        tag(root, "IL: t_IL counts in full", 200.0, 10.0, during(3, 4))
        tag(root, "HfO2: t_hk x 3.9/k", 400.0, 60.0, during(3, 4))

    dscene(name_of(stem), 4, [pose(-300.0, 40.0, 1300.0, 0.25, 0.16), pose(300.0, 40.0, 1200.0, 0.15, 0.10),
                              pose(20.0, 40.0, 2050.0, 0.18, 0.14), pose(330.0, 40.0, 950.0, 0.22, 0.14)], body)


def zoom_d(stem="zoom_d"):
    """Work-function metals and dipoles: the NMOS's TiAlC(N), the PMOS's TiN, a La cap, both."""
    NX, PX_ = -620.0, 620.0

    def body(root, m):
        D.frame(root, m, cx=NX, hw=560.0)
        wn = D.trench(root, m, cx=NX, stack=D.films(dipole=True), pre="n")
        D.frame(root, m, cx=PX_, hw=560.0, sd_mat="d_pplus")
        wp = D.trench(root, m, cx=PX_, stack=D.films(wfm="d_tin"), pre="p")
        tag(root, "TiAlC(N): Al-rich NMOS metal", wn["wfm"][0] + 12.0, 250.0, during(0, 1))
        tag(root, "n+ source", NX - 400.0, -60.0, during(0, 1))
        tag(root, "TiN: thick PMOS metal", wp["wfm"][0] + 12.0, 250.0, during(1, 2))
        tag(root, "p+ source", PX_ - 400.0, -60.0, during(1, 2))
        tag(root, "La dipole: lowers nFET Vt", wn["dip"][0] + 3.0, 200.0, during(2, 3))
        tag(root, "NMOS: low Vt", NX, 480.0, during(3, 4))
        tag(root, "PMOS: its own Vt", PX_, 480.0, during(3, 4))

    dscene(name_of(stem), 4, [pose(NX, 60.0, 1600.0, 0.30, 0.20), pose(PX_, 60.0, 1600.0, 0.30, 0.20),
                              pose(NX - 110.0, 120.0, 700.0, 0.35, 0.22), pose(0.0, 60.0, 3300.0, 0.15, 0.14)], body)


def zoom_e(stem="zoom_e"):
    """The stack in a nanosheet gap: the wrapped sheets, what fits, Vt varies, the channel."""

    def body(root, m):
        ga = D.group("rig_a", root, during(0, 2))
        sh, _ = D.gaa(ga, m, pre="a")
        gb = D.group("rig_b", root, during(2, 3))
        D.gaa(gb, m, pre="b", thin=1)
        hw = D.SHEET_HW
        # beat 3: the same sheets cut along the channel, electrons riding each from source to drain
        gc = D.group("rig_c", root, during(3, 4))
        D.gaa_side(gc, m, sh)
        for i, (s0, s1) in enumerate(sh):
            y = (s0 + s1) / 2
            D.path_run(root, m, f"cur{i}", D.arc((-520.0, y, 24.0), (520.0, y, 24.0), 0.0, 6), 6, 3,
                       0.05 + 0.04 * i, 0.85, 60, "d_elec", "d_trk_e", 12.0)
        mid = (sh[1][0] + sh[1][1]) / 2
        tag(root, "Si nanosheet", 0.0, mid, during(0, 1))
        tag(root, "gate on all four sides", hw + 30.0, sh[0][1] + 20.0, during(0, 1))
        tag(root, "W fill between sheets", 0.0, (sh[0][1] + sh[1][0]) / 2, during(0, 1))
        tag(root, "IL ~0.5 nm", -hw + 40.0, sh[1][1] + 4.0, during(1, 2))
        tag(root, "HfO2 ~1.8 nm", -hw + 120.0, sh[1][1] + 19.0, during(1, 2))
        tag(root, "work-function metal", -hw + 200.0, sh[1][1] + 41.0, during(1, 2))
        tag(root, "thinner metal: Vt shifts", hw + 35.0, mid, during(2, 3))
        tag(root, "n+ source", -420.0, 120.0, during(3, 4))
        tag(root, "n+ drain", 420.0, 120.0, during(3, 4))
        tag(root, "gate between the sheets", 0.0, (sh[1][1] + sh[2][0]) / 2, during(3, 4))
        tag(root, "electrons ride every sheet", 250.0, (sh[0][0] + sh[0][1]) / 2, during(3, 4))

    dscene(name_of(stem), 4, [pose(0.0, 200.0, 1700.0, 0.20, 0.14), pose(-60.0, sh_mid(), 650.0, 0.15, 0.10),
                              pose(0.0, 200.0, 1700.0, 0.20, 0.14), pose(0.0, 220.0, 2000.0, 0.25, 0.16)], body)


def sh_mid():
    """The y of the middle sheet's top film, for zoom e's close pose."""
    wrap = sum(t for _, t, _ in D.RING)
    y0 = wrap + 34.0 * 0.6 + (D.SHEET_T + 2 * wrap + 34.0)
    return y0 + D.SHEET_T + 30.0


# ---- sections 1-10: detailed close-up rigs (chip_gate_stack_detail.py) -------------------------
# Each section is its own cut-away transistor, gate trench or nanosheet stack, framed to fill the
# left pane; the whole chip is the overview's job.

import chip_gate_stack_detail as D  # noqa: E402


def dscene(name, beats, poses, body):
    """A section scene: body(root, m) builds a close-up rig, the camera glides through `poses`."""
    m, root = start(name, beats, page="chip")
    C.mats(m)
    mats(m)
    D.mats(m)
    body(root, m)
    C.glide_camera(root, poses)
    finish(name, page="chip")


def pose(x, y, d, yaw=0.0, pitch=0.12):
    return ((x, y, 0.0), d, yaw, pitch)


def sp(a, b):
    return D.span(a, b)


WHOLE_RMG = pose(90.0, 20.0, 2300.0, 0.38, 0.24)  # one RMG transistor, three-quarter view


def sec1(stem="sec1"):
    """What happens: the empty gate trench, ALD grows the IL and HfO2, then the metals and the fill,
    polished flat."""

    def body(root, m):
        D.frame(root, m)
        on = {"il": sp((1, 0.10), 3), "hk": sp((1, 0.45), 3), "cap": sp((2, 0.05), 3),
              "wfm": sp((2, 0.18), 3), "bar": sp((2, 0.30), 3), "fill": sp((2, 0.42), 3)}
        D.trench(root, m, on=on)
        D.part("overburden", (-640.0, D.H, -D.DZ), (640.0, D.H + 46.0, 0.0), m["d_w"], root,
               sp((2, 0.42), (2, 0.72)))
        D.part("slurry", (-660.0, D.H + 46.0, -D.DZ), (660.0, D.H + 60.0, 6.0), m["d_slurry"], root,
               sp((2, 0.60), (2, 0.72)))
        # ALD precursor pulses settling on the trench floor and walls
        for k, x in enumerate((-150.0, -60.0, 30.0, 120.0)):
            D.electrons(root, m, f"prec{k}", [(x, 560.0, 20.0), (x, 30.0, 20.0)], 4, 1, 0.05 + 0.04 * k,
                        0.70, 60, "d_ald", 11.0)
        tag(root, "trench: dummy gate pulled out", 0.0, 250.0, during(0, 1))
        tag(root, "nitride spacer", -242.0, 330.0, during(0, 1))
        tag(root, "n+ source, raised epi", -420.0, -60.0, during(0, 1))
        tag(root, "n+ drain", 420.0, -60.0, during(0, 1))
        tag(root, "ILD0 oxide", 450.0, 260.0, during(0, 1))
        tag(root, "ALD precursor pulses", 60.0, 420.0, sp(1, (1, 0.6)))
        tag(root, "IL SiOx ~0.5 nm, floor only", -110.0, 6.0, sp((1, 0.15), 2))
        tag(root, "HfO2 ~1.8 nm, floor and walls", -205.0, 200.0, sp((1, 0.5), 2))
        tag(root, "W overfill", 300.0, D.H + 30.0, sp((2, 0.42), (2, 0.72)))
        tag(root, "CMP polishes it flat", -300.0, D.H + 55.0, sp((2, 0.60), (2, 0.72)))
        tag(root, "TiN / TiAlC / TiN metals", -150.0, 200.0, sp((2, 0.72), 3))
        tag(root, "W fill: the gate electrode", 0.0, 300.0, sp((2, 0.72), 3))

    dscene(name_of(stem), 3, [WHOLE_RMG, pose(-100.0, 90.0, 900.0, 0.30, 0.22),
                              pose(0.0, 170.0, 1750.0, 0.30, 0.22)], body)


def sec2(stem="sec2"):
    """The replacement-metal-gate flow: dummy poly, source/drain and anneal, ILD0 and the poly pull,
    then the high-k and metal stack in the trench."""

    def body(root, m):
        D.frame(root, m, ild=sp(2, 4), sd=sp(1, 4))
        D.dummy(root, m, ivs=sp(0, (2, 0.5)))
        D.anneal(root, m, ivs=sp((1, 0.35), (1, 0.85)))
        D.part("ild_cmp", (-660.0, D.H, -D.DZ), (660.0, D.H + 14.0, 6.0), m["d_slurry"], root,
               sp((2, 0.05), (2, 0.35)))
        D.part("pull_glow", (-220.0, 0.0, -D.DZ), (220.0, D.H, 6.0), m["d_hl"], root, sp((2, 0.5), (2, 0.8)))
        on = {"il": sp((3, 0.05), 4), "hk": sp((3, 0.15), 4), "cap": sp((3, 0.28), 4),
              "wfm": sp((3, 0.38), 4), "bar": sp((3, 0.48), 4), "fill": sp((3, 0.58), 4)}
        D.trench(root, m, on=on)
        tag(root, "dummy polysilicon gate", 0.0, 260.0, during(0, 1))
        tag(root, "thin SiO2 under it", -150.0, 5.0, during(0, 1))
        tag(root, "nitride spacers", 242.0, 330.0, during(0, 1))
        tag(root, "n+ source/drain epi", -420.0, 0.0, during(1, 2))
        tag(root, "anneal ~1000 C", 420.0, -120.0, sp((1, 0.35), (1, 0.85)))
        tag(root, "ILD0 oxide, polished", 450.0, 260.0, sp(2, (2, 0.5)))
        tag(root, "poly etched out: a trench", 0.0, 250.0, sp((2, 0.5), 3))
        tag(root, "IL + HfO2 + metals line it", -205.0, 150.0, sp((3, 0.2), 4))
        tag(root, "W fill, polished to the top", 0.0, 300.0, sp((3, 0.6), 4))

    dscene(name_of(stem), 4, [WHOLE_RMG, pose(0.0, -20.0, 2150.0, 0.30, 0.22), WHOLE_RMG,
                              pose(-40.0, 150.0, 1300.0, 0.30, 0.22)], body)


STAIR = 34.0


def ztag(root, text, at, ivs):
    label(text, at, root, ivs)


def film_pins(w, stack):
    """Pin points on each film of a stepped trench: (wall x, floor y, front z) by key."""
    out = {}
    for i, (k, t, _, kind) in enumerate(stack):
        x0, _, y0 = w[k]
        tt = t or 0.0
        out[k] = (x0 + tt / 2, y0 + tt / 2, -STAIR * i)
    return out


def stair_rig(root, m, dipole=False):
    stack = D.films(dipole=dipole)
    D.frame(root, m)
    w = D.trench(root, m, stack=stack, stair=STAIR)
    return w, film_pins(w, stack)


def sec3(stem="sec3"):
    """One replacement gate in section, as a stepped cut-away: each film's front face sits a step
    behind the one under it, so all of them show."""

    def body(root, m):
        w, p = stair_rig(root, m, dipole=True)
        ztag(root, "IL SiOx ~0.5 nm", (-40.0, p["il"][1], p["il"][2]), during(0, 1))
        ztag(root, "HfO2 high-k, k ~20-25", (-40.0, p["hk"][1], p["hk"][2]), during(0, 1))
        ztag(root, "La dipole cap", (p["dip"][0], 160.0, p["dip"][2]), during(0, 1))
        ztag(root, "TiN cap", (p["cap"][0], 150.0, p["cap"][2]), during(1, 2))
        ztag(root, "TiAlC(N): NMOS work-function", (p["wfm"][0], 260.0, p["wfm"][2]), during(1, 2))
        ztag(root, "TiN barrier: stops W", (p["bar"][0], 330.0, p["bar"][2]), during(2, 3))
        ztag(root, "W fill: low resistance", (0.0, 260.0, p["fill"][2]), during(2, 3))
        ztag(root, "nitride spacer", (-242.0, 330.0, 0.0), during(3, 4))
        ztag(root, "ILD0 oxide", (-450.0, 260.0, 0.0), during(3, 4))
        ztag(root, "U-shaped films", (-p["hk"][0], 360.0, p["hk"][2]), during(3, 4))
        ztag(root, "channel under the floor", (0.0, -30.0, 0.0), during(3, 4))
        del w

    dscene(name_of(stem), 4, [pose(-110.0, 60.0, 640.0, 0.50, 0.30), pose(-120.0, 200.0, 900.0, 0.50, 0.26),
                              pose(-60.0, 260.0, 1000.0, 0.45, 0.24), pose(60.0, 40.0, 2000.0, 0.40, 0.22)], body)


def sec4(stem="sec4"):
    """Gate-first (top) against gate-last (bottom) through the same source/drain anneal."""
    DY = 900.0  # the gate-first transistor sits this far above the gate-last one

    def body(root, m):
        top = empty("gate_first", root)
        D.frame(top, m)
        D.flat_stack(top, m)
        D.part("hot_hk", (-220.0, 12.0, -D.DZ), (220.0, 38.0, 4.0), m["d_hot"], top, sp((1, 0.3), 3))
        D.anneal(top, m, ivs=sp((1, 0.15), (1, 0.85)), pre="an_t")
        top.location = P(0.0, DY, 0.0)
        D.frame(root, m)
        D.dummy(root, m, ivs=sp(0, (2, 0.35)))
        on = {k: sp((2, 0.35 + 0.08 * i), 3) for i, k in enumerate(("il", "hk", "cap", "wfm", "bar", "fill"))}
        D.trench(root, m, on=on, pre="r")
        D.anneal(root, m, ivs=sp((1, 0.15), (1, 0.85)), pre="an_b")
        tag(root, "GATE-FIRST", -560.0, DY + 420.0, during(0, 3))
        tag(root, "GATE-LAST", -560.0, 420.0, during(0, 3))
        tag(root, "HfO2 + metal, poly cap", 120.0, DY + 200.0, during(0, 1))
        tag(root, "dummy poly", 0.0, 220.0, during(0, 1))
        tag(root, "anneal ~1000 C", 420.0, DY - 80.0, sp((1, 0.15), (1, 0.85)))
        tag(root, "anneal ~1000 C", 420.0, -80.0, sp((1, 0.15), (1, 0.85)))
        tag(root, "high-k heated: Vt shifts", 120.0, DY + 25.0, sp((1, 0.3), 3))
        tag(root, "dummy poly takes the heat", 0.0, 220.0, sp(1, (2, 0.35)))
        tag(root, "poly out, stack in after", 100.0, 200.0, sp((2, 0.35), 3))

    dscene(name_of(stem), 3, [pose(0.0, 480.0, 3500.0, 0.25, 0.12), pose(0.0, 480.0, 3400.0, 0.25, 0.12),
                              pose(0.0, 480.0, 3400.0, 0.25, 0.12)], body)


def eot_columns(root, m, ivs_left=None, ivs_right=None):
    L = D.group("left", root, ivs_left)
    yl = D.column(L, m, -300.0, [("sio2", 1.2, "d_sio2")], "l", 300.0, 300.0)
    R = D.group("right", root, ivs_right)
    yr = D.column(R, m, 300.0, [("il", 0.5, "d_il"), ("hk", 1.8, "d_hfo2")], "r", 300.0, 300.0)
    return yl, yr


def tunnel(root, m, name, cx, top, n, b0, b1):
    """Electrons tunnelling up from the channel through the dielectric into the gate."""
    for b in range(b0, b1):
        for k, dx in enumerate((-120.0, -40.0, 40.0, 120.0)[:max(1, n)]):
            D.electrons(root, m, f"{name}{b}_{k}", [(cx + dx, -40.0, 14.0), (cx + dx, top + 60.0, 14.0)],
                        max(1, n // 2), b, 0.05 + 0.05 * k, 0.85, 50, "d_elec", 10.0)


def sec5(stem="sec5"):
    """Why the oxide had to go: SiO2 at 1.2 nm tunnels; IL + HfO2 is twice as thick for more
    capacitance; the rulers compare physical thickness and EOT; the IL is most of the EOT now."""

    def body(root, m):
        yl, yr = eot_columns(root, m)
        tunnel(root, m, "lk", -300.0, yl["gate"], 8, 0, 4)
        D.electrons(root, m, "rk1", [(300.0, -40.0, 14.0), (300.0, yr["gate"] + 60.0, 14.0)], 1, 1, 0.4, 0.5, 50)
        D.electrons(root, m, "rk2", [(240.0, -40.0, 14.0), (240.0, yr["gate"] + 60.0, 14.0)], 1, 3, 0.4, 0.5, 50)
        # rulers: physical thickness (cyan) and EOT (pink), beside each dielectric
        for cx, phys, eot in ((-300.0, 1.2, 1.2), (300.0, 2.3, 0.85)):
            x = cx + D.EOT_HW + 24.0
            D.part(f"phys{cx:.0f}", (x, 0.0, -20.0), (x + 22.0, phys * D.NM, 10.0), m["d_phys"], root, sp(2, 4))
            D.part(f"eot{cx:.0f}", (x + 34.0, 0.0, -20.0), (x + 56.0, eot * D.NM, 10.0), m["d_eot"], root, sp(2, 4))
        D.part("il_hl", (300.0 - D.EOT_HW - 4, -2.0, -40.0), (300.0 + D.EOT_HW + 4, 22.0, 10.0), m["d_hl"], root,
               sp(3, 4))
        rx = 300.0 + D.EOT_HW + 24.0
        lx = -300.0 + D.EOT_HW + 24.0
        tag(root, "SiO2 1.2 nm: ~5 atoms thick", -440.0, 24.0, during(0, 3))
        tag(root, "electrons tunnel through", -260.0, 30.0, during(0, 1))
        tag(root, "metal gate", -300.0, yl["gate"] + 180.0, during(0, 1))
        tag(root, "silicon channel", -300.0, -170.0, during(0, 1))
        tag(root, "IL 0.5 + HfO2 1.8 nm", 400.0, 50.0, during(1, 3))
        tag(root, "~2x thicker: far less leak", 300.0, 200.0, during(1, 2))
        tag(root, "physical 2.3 nm", rx + 11.0, 92.0, during(2, 3))
        tag(root, "EOT ~0.85 nm", rx + 45.0, 34.0, during(2, 3))
        tag(root, "physical = EOT = 1.2 nm", lx + 30.0, 48.0, during(2, 3))
        tag(root, "IL: ~0.5 of the ~0.85 nm", 200.0, 10.0, during(3, 4))
        tag(root, "HfO2 adds only ~0.35 nm", 380.0, 60.0, during(3, 4))

    dscene(name_of(stem), 4, [pose(-300.0, 40.0, 1300.0, 0.25, 0.16), pose(20.0, 40.0, 2050.0, 0.18, 0.14),
                              pose(80.0, 40.0, 2050.0, 0.0, 0.10), pose(330.0, 40.0, 950.0, 0.22, 0.14)], body)


def sec6(stem="sec6"):
    """Threshold tuning in a nanosheet gate: the wrapped sheets, a La dipole on the nFET stack, an
    Al dipole on the pFET stack."""
    NX, PX_ = -400.0, 400.0

    def body(root, m):
        sn, bn = D.gaa(root, m, cx=NX, pre="n")
        spp, bp = D.gaa(root, m, cx=PX_, wfm="d_tin", pre="p")
        D.dipole_rings(root, m, NX, sn, "d_dip_la", sp((1, 0.15), 3), "n")
        D.dipole_rings(root, m, PX_, spp, "d_dip_al", sp((2, 0.15), 3), "p")
        mid = (sn[1][0] + sn[1][1]) / 2
        tag(root, "Si nanosheet ~5 nm", NX, mid, during(0, 1))
        tag(root, "IL + HfO2 + metal, all round", NX + D.SHEET_HW + 30.0, sn[0][1] + 20.0, during(0, 1))
        tag(root, "W fill in the gap", NX, (sn[0][1] + sn[1][0]) / 2, during(0, 1))
        tag(root, "nFET: TiAlC metal", NX - D.SHEET_HW - 40.0, sn[2][0], during(1, 3))
        tag(root, "La dipole: lowers nFET Vt", NX + D.SHEET_HW + 10.0, sn[1][1] + 10.0, sp((1, 0.15), 2))
        tag(root, "pFET: TiN metal", PX_ + D.SHEET_HW + 40.0, spp[0][0], during(2, 3))
        tag(root, "Al dipole: shifts Vt other way", PX_ - D.SHEET_HW - 10.0, spp[1][1] + 10.0, sp((2, 0.15), 3))
        del bn, bp

    dscene(name_of(stem), 3, [pose(NX - 60.0, 190.0, 1750.0, 0.10, 0.14), pose(NX - 60.0, 190.0, 1750.0, 0.10, 0.14),
                              pose(0.0, 190.0, 2900.0, 0.12, 0.12)], body)


def sec7(stem="sec7"):
    """By the numbers: the SiO2 limit, Intel's 45 nm HfO2, ALD one cycle at a time."""

    def body(root, m):
        yl, yr = eot_columns(root, m)
        tunnel(root, m, "lk", -300.0, yl["gate"], 8, 0, 2)
        D.electrons(root, m, "rk1", [(300.0, -40.0, 14.0), (300.0, yr["gate"] + 60.0, 14.0)], 1, 1, 0.4, 0.5, 50)
        # beat 2: the HfO2 laid down one ALD cycle (~0.1 nm) at a time, in front of a dark gap
        n = 18
        t = 1.8 * D.NM / n
        for k in range(n):
            y = yr["hk"] + k * t
            D.part(f"cyc{k}", (300.0 - D.EOT_HW - 3, y, -30.0), (300.0 + D.EOT_HW + 3, y + t, 6.0),
                   m["d_ald"] if k % 2 else m["d_hfo2"], root, sp((2, 0.06 + 0.045 * k), 3))
        D.part("cyc_gap", (300.0 - D.EOT_HW - 2, yr["hk"], -29.0), (300.0 + D.EOT_HW + 2, yr["gate"], 3.0),
               m["d_void"], root, sp(2, 3))
        tag(root, "SiO2 ~1.2 nm: the 90 nm limit", -440.0, 24.0, during(0, 2))
        tag(root, "~10x more leak per 0.2 nm thinner", -300.0, 150.0, during(0, 1))
        tag(root, "Intel 45 nm: HfO2, EOT ~1 nm", 420.0, 60.0, during(1, 2))
        tag(root, ">10x less gate leakage", 300.0, 200.0, during(1, 2))
        tag(root, "one ALD cycle: ~0.1 nm", 420.0, 60.0, during(2, 3))
        tag(root, "~18 cycles for ~1.8 nm", 200.0, 95.0, during(2, 3))

    dscene(name_of(stem), 3, [pose(-300.0, 40.0, 1300.0, 0.25, 0.16), pose(20.0, 40.0, 2050.0, 0.18, 0.14),
                              pose(300.0, 50.0, 700.0, 0.20, 0.12)], body)


def sec8(stem="sec8"):
    """Who makes it: the films each toolmaker lays down, then the foundries that build the gate."""

    def body(root, m):
        w, p = stair_rig(root, m)
        ztag(root, "ASM: ALD of the HfO2", (-40.0, p["hk"][1], p["hk"][2]), during(0, 1))
        ztag(root, "IL grown on the silicon", (-40.0, p["il"][1], p["il"][2]), during(0, 1))
        ztag(root, "Applied: TiN (Endura)", (p["cap"][0], 150.0, p["cap"][2]), during(1, 2))
        ztag(root, "Lam: ALD tungsten fill", (0.0, 260.0, p["fill"][2]), during(1, 2))
        ztag(root, "TEL: furnace and ALD tools", (-450.0, 200.0, 0.0), during(2, 3))
        ztag(root, "TSMC 28 nm, Intel 45 nm: gate-last", (0.0, 330.0, p["fill"][2]), during(2, 3))
        del w

    dscene(name_of(stem), 3, [pose(-110.0, 60.0, 640.0, 0.50, 0.30), pose(-80.0, 200.0, 1000.0, 0.45, 0.26),
                              pose(60.0, 40.0, 2000.0, 0.40, 0.22)], body)


def sec9(stem="sec9"):
    """Chokepoints: work-function thickness spread in nanosheet gaps, the IL thickness, a void in
    a narrow fill. Three rigs at the origin, one per beat."""

    def body(root, m):
        g0 = D.group("rig0", root, during(0, 1))
        sh, _ = D.gaa(g0, m, cx=0.0, pre="v", thin=1)
        g1 = D.group("rig1", root, during(1, 2))
        D.frame(g1, m)
        D.trench(g1, m, pre="t1")
        D.part("il_hl", (-224.0, -2.0, -40.0), (224.0, 14.0, 10.0), m["d_hl"], g1)
        g2 = D.group("rig2", root, during(2, 3))
        D.frame(g2, m, wt=130.0)
        D.trench(g2, m, wt=130.0, pre="t2")
        D.box("void", (-9.0, 150.0, -D.DZ), (9.0, 340.0, 3.0), m["d_void"], g2)
        tag(root, "thinner metal here: Vt shifts", D.SHEET_HW + 35.0, (sh[1][0] + sh[1][1]) / 2, during(0, 1))
        tag(root, "gaps only a few nm wide", 0.0, (sh[1][1] + sh[2][0]) / 2, during(0, 1))
        tag(root, "IL: +0.1 nm = +0.1 nm EOT", -120.0, 6.0, during(1, 2))
        tag(root, "must match across the wafer", 60.0, 6.0, during(1, 2))
        tag(root, "seam/void in the W fill", 0.0, 260.0, during(2, 3))
        tag(root, "narrow gate: less room", -100.0, 380.0, during(2, 3))

    dscene(name_of(stem), 3, [pose(0.0, 190.0, 1650.0, 0.25, 0.14), pose(-60.0, 40.0, 800.0, 0.35, 0.22),
                              pose(0.0, 150.0, 1250.0, 0.30, 0.18)], body)


def sec10(stem="sec10"):
    """Sources: the finished gate, with each beat on the films its sources describe."""

    def body(root, m):
        w, p = stair_rig(root, m)
        ztag(root, "[1-2] Intel 45 nm HKMG, 2007", (0.0, 330.0, p["fill"][2]), during(0, 1))
        ztag(root, "[3] HfO2 and IL: MRS, IEEE", (-40.0, p["hk"][1], p["hk"][2]), during(1, 2))
        ztag(root, "[4] gate-first vs gate-last", (-242.0, 330.0, 0.0), during(1, 2))
        ztag(root, "[5] ASM: ALD", (-40.0, p["hk"][1], p["hk"][2]), during(2, 3))
        ztag(root, "[7] Applied: TiN", (p["cap"][0], 150.0, p["cap"][2]), during(2, 3))
        ztag(root, "[6, 8] Lam: W, Mo fill", (0.0, 260.0, p["fill"][2]), during(2, 3))
        del w

    dscene(name_of(stem), 3, [pose(60.0, 40.0, 2000.0, 0.40, 0.22), pose(-120.0, 120.0, 1000.0, 0.45, 0.24),
                              pose(-80.0, 160.0, 1100.0, 0.45, 0.24)], body)


SCENES = {
    "zoom_a": zoom_a, "zoom_b": zoom_b, "zoom_c": zoom_c, "zoom_d": zoom_d, "zoom_e": zoom_e,
    "sec1": sec1, "sec2": sec2, "sec3": sec3, "sec4": sec4, "sec5": sec5, "sec6": sec6,
    "sec7": sec7, "sec8": sec8, "sec9": sec9, "sec10": sec10,
}


if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None
    if which is None or "overview" in which:
        build()
    for key in (SCENES if which is None else which):
        if key != "overview":
            SCENES[key]()
