"""CHIP pictures for the GATE STACK node: the overview, zoom-ins a-e and sections 1-10.

Run from the repo root (all of them, or name some after `--`):

    blender -b --factory-startup --python tools/pbr3d/blender/chip_gate_stack.py
    blender -b --factory-startup --python tools/pbr3d/blender/chip_gate_stack.py -- zoom_a sec4

Writes blender/chip_gate_stack[_zoom_<key>|_sec<N>].blend and assets/chip_gate_stack[...].glb.
One beat is 8 s.

The overview (beats 0-5): the whole chip, then in on the NMOS gate stack.

  zoom a  the layers, from interlayer to fill (4 beats)
  zoom b  gate-last: dummy poly, S/D anneal, poly pull, the stack goes in (4 beats)
  zoom c  EOT: thin SiO2 leaks, HfO2 is thick at the same EOT, Intel 45 nm (4 beats)
  zoom d  work-function metals and dipoles: NMOS TiAlC(N), PMOS TiN, La cap, both (4 beats)
  zoom e  the stack in a nanosheet gap: wrapped sheets, fit, Vt varies, channel (4 beats)
  sec 1   what happens: the whole chip, then the layers grown by ALD (3 beats)
  sec 2   the replacement-metal-gate flow (same scene as zoom b)
  sec 3   one replacement gate in section (same scene as zoom a)
  sec 4   gate-first versus gate-last (3 beats)
  sec 5   EOT and leakage (same scene as zoom c)
  sec 6   threshold tuning in a nanosheet gate: a dipole on one sheet, another on the next (3 beats)
  sec 7   by the numbers: SiO2 limit, HfO2 EOT, the ALD market (3 beats)
  sec 8   who makes it: ASM, Applied and Lam, then TEL, TSMC and Intel (3 beats)
  sec 9   chokepoints: Vt variation in the gaps, IL thickness, fill voids (3 beats)
  sec 10  sources: the whole chip, slow pull-back, the sources as labels (3 beats)

The gate stack is built here (chip_kit's gate is two plain boxes). Silicon, contacts, wiring,
bumps and the PMOS come from chip_kit. Layers are drawn at about 10 mm per nm, so the stack is
thicker than life next to the gate width; the gate itself is drawn wider than a real one.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chip_kit as C  # noqa: E402
from sand_overview import F, ball, box, empty, label, mat, show, tube  # noqa: E402
from sand_zooms import finish, start  # noqa: E402
from chip_kit import overlay, route, stream_of  # noqa: E402

BEATS = 6
NAME = "gate_stack"
CX = C.NMOS_X  # the gate is centred on the NMOS
PX = C.PMOS_X
GH = C.GATE_HALF  # half the gate width
SD = C.SD  # source and drain sit this far either side of the gate

# gate stack bands on the silicon, (bottom, top) in y, mm
IL = (0.0, 5.0)  # interfacial SiOx, about 0.5 nm
HFO2 = (5.0, 23.0)  # HfO2 high-k, about 1.8 nm
SIO2 = (5.0, 17.0)  # SiO2 about 1.2 nm, at the same 10 mm per nm
TIALC = (23.0, 35.0)  # TiAlC(N) work-function metal (NMOS)
TIN = (35.0, 41.0)  # TiN glue and barrier
FILL = (41.0, 120.0)  # tungsten fill up to the gate top (C.contacts plugs land on it)
FILM = {"hfo2": (HFO2, "hfo2"), "sio2": (SIO2, "sio2")}

# the field and the inversion layer sit in front of the cut plane, so they show
FIELD_Z = 14.0
EOT_Y = (150.0, 160.0)  # the reference SiO2 film, floating above the gate

# GAA: three nanosheets, with the gate in the four gaps between and around them
GAA_SHEETS = [(40.0, 54.0), (104.0, 118.0), (168.0, 182.0)]
GAA_GAPS = [(0.0, 40.0), (54.0, 104.0), (118.0, 168.0), (182.0, 222.0)]

# ---- the overview -------------------------------------------------------------------------

# beat windows
GATE_ON = [(F(2, 0.1), F(5, 0.0))]
FIELD_ON = [(F(2, 0.2), F(5, 0.0))]
INV_ON = [(F(3, 0.3), F(5, 0.0))]
EOT_ON = [(F(4, 0.0), F(5, 0.0))]
HL_ON = [(F(0, 0.0), F(1, 0.2)), (F(5, 0.4), F(6, 0.0))]

# (target, distance, yaw, pitch) per beat
WHOLE = C.WHOLE
ZOOM = ((CX, 55.0, 0.0), 600.0, 0.0, 0.08)
POSES = [
    WHOLE,
    ZOOM,
    ((CX, 45.0, 0.0), 560.0, 0.0, 0.08),
    ((CX, 45.0, 0.0), 520.0, 0.0, 0.08),
    ((CX, 100.0, 0.0), 760.0, 0.0, 0.08),
    WHOLE,
]


def mats(m):
    m["il"] = mat("chip_gate_stack_il", (0.70, 0.76, 0.84), rough=0.5)
    m["hfo2"] = mat("chip_gate_stack_hfo2", (0.98, 0.86, 0.30), rough=0.35)
    m["sio2"] = mat("chip_gate_stack_sio2", (0.90, 0.92, 0.96), rough=0.4)
    m["tialc"] = mat("chip_gate_stack_tialc", (0.50, 0.58, 0.70), metal=0.9, rough=0.3)
    m["tin"] = mat("chip_gate_stack_tin", (0.85, 0.66, 0.32), metal=0.9, rough=0.3)
    m["poly"] = mat("chip_gate_stack_poly", (0.50, 0.42, 0.34), rough=0.6)
    m["ild"] = mat("chip_gate_stack_ild", (0.52, 0.58, 0.72), rough=0.5)
    m["sheet"] = mat("chip_gate_stack_sheet", (0.36, 0.44, 0.58), metal=0.2, rough=0.4)
    m["dip"] = mat("chip_gate_stack_dip", (0.80, 0.55, 1.0), emit=(0.75, 0.50, 1.0), strength=2.0)
    m["void"] = mat("chip_gate_stack_void", (0.04, 0.04, 0.05), rough=0.9)
    m["glow"] = mat("chip_gate_stack_glow", (1.0, 0.72, 0.35), emit=(1.0, 0.65, 0.25), strength=1.0, alpha=0.22)
    m["hl"] = mat("chip_gate_stack_hl", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=1.0, alpha=0.16)
    m["ghost"] = mat("chip_gate_stack_ghost", (0.70, 0.85, 1.0), emit=(0.55, 0.80, 1.0), strength=1.0, alpha=0.35)
    # the zoom-ins highlight a band lightly, so its colour still reads through
    m["hl_soft"] = mat("chip_gate_stack_hl_soft", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=0.6, alpha=0.07)


def gate_stack(root, m):
    """The NMOS: n+ source and drain, the layered gate over the channel, and the overlays
    (gate glow, field lines, inversion channel, the SiO2-equivalent reference film)."""
    g = empty("nmos", root)
    for sgn in (-1, 1):
        x = CX + sgn * SD
        box(f"sd{sgn}", (x - 70, -90, -240), (x + 70, 6, 0), m["c_nplus"], g)

    # the layers, each a slab from the channel up, front faces on the cut plane z = 0
    wide = (CX - GH - 8, CX + GH + 8)
    gate = (CX - GH, CX + GH)
    box("il", (wide[0], IL[0], -240), (wide[1], IL[1], 0), m["il"], g)
    box("hfo2", (wide[0], HFO2[0], -240), (wide[1], HFO2[1], 0), m["hfo2"], g)
    box("tialc", (gate[0], TIALC[0], -240), (gate[1], TIALC[1], 0), m["tialc"], g)
    box("tin", (gate[0], TIN[0], -240), (gate[1], TIN[1], 0), m["tin"], g)
    box("w_fill", (gate[0], FILL[0], -240), (gate[1], FILL[1], 0), m["c_w"], g)

    # gate on: the whole stack glows
    overlay(g, "gate_glow", (wide[0], -2, -246), (wide[1], FILL[1] + 6, 6), m["glow"], GATE_ON)

    # field lines from the gate down through the stack, in front of the cut plane
    fld = empty("field_g", g)
    for dx in (-60.0, 0.0, 60.0):
        tube(f"field{dx:.0f}", (CX + dx, FILL[1] + 10, FIELD_Z), (CX + dx, -8.0, FIELD_Z), 2.5, m["c_gate_on"], fld, verts=8)
    show(fld, FIELD_ON)

    # the inversion layer: a thin band at the silicon surface under the gate
    overlay(g, "inversion", (gate[0], -10.0, -230), (gate[1], 0.0, 3.0), m["c_chan"], INV_ON)

    # the SiO2 film with the same capacitance (EOT ~1 nm class), floating above the gate
    overlay(g, "eot_sio2", (wide[0], EOT_Y[0], -240), (wide[1], EOT_Y[1], 0), m["ghost"], EOT_ON)

    # highlight the NMOS on the whole chip (beats 0 and 5 only)
    overlay(g, "nmos_hl", (CX - 330, -140, -250), (CX + 330, 150, 14), m["hl"], HL_ON)
    return g


def electrons(root, m):
    """Electrons pulled up out of the silicon under the gate (beat 3)."""
    for k, dx in enumerate((-60.0, 0.0, 60.0)):
        s, p = route([(CX + dx, -170.0, FIELD_Z), (CX + dx, -12.0, FIELD_Z)])
        stream_of(root, f"elec{k}", 6, s, p, 14, m["c_dot_sig"], 3, 0.10, 0.60, 60)


def labels(root):
    whole = [(F(0, 0), F(1, 0.2)), (F(5, 0.4), F(6, 0.0))]
    label("NMOS gate stack", (CX, 270.0, 0), root, whole)

    b1 = [(F(1, 0.35), F(2, 0.0))]
    label("W fill: gate metal", (CX + 110.0, 95.0, 0), root, b1)
    label("HfO2 high-k", (CX + 110.0, 14.0, 0), root, b1)
    label("IL SiOx ~0.5 nm", (CX - 110.0, 2.0, 0), root, b1)
    label("TiAlC(N) work-function", (CX - 110.0, 29.0, 0), root, b1)

    b2 = [(F(2, 0.2), F(3, 0.0))]
    label("gate high: field on", (CX, 150.0, 0), root, b2)
    label("field through HfO2", (CX - 135.0, 14.0, 0), root, b2)

    b3 = [(F(3, 0.3), F(4, 0.0))]
    label("electrons pulled up", (CX - 135.0, -30.0, 0), root, b3)
    label("inversion channel", (CX + 135.0, -4.0, 0), root, b3)

    b4 = [(F(4, 0.1), F(5, 0.0))]
    label("HfO2 1.5-2 nm, thick", (CX + 135.0, 14.0, 0), root, b4)
    label("EOT ~1 nm: as SiO2", (CX, 180.0, 0), root, b4)


def build(name=NAME, poses=POSES):
    m, root = start(name, BEATS, page="chip")
    C.mats(m)
    mats(m)
    C.silicon(root, m)
    gate_stack(root, m)
    C.transistor(root, m, C.PMOS_X, False)
    C.contacts(root, m)
    C.wiring(root, m)
    C.bumps(root, m)
    electrons(root, m)
    labels(root)
    C.glide_camera(root, poses)


# ---- zoom-ins and sections ------------------------------------------------------------------
# Every scene below is the same chip: silicon, the NMOS gate built from `gate()` layers, the
# PMOS and the contacts from chip_kit. A layer is (name, bottom, top, material, intervals, wide,
# zmax): `intervals` switch it on (default ALL), `wide` picks its width (False: the gate, True: a
# little wider, a number: a half-width, a tuple: the two side spans), and `zmax` lifts an overlay
# in front of the cut plane.

ALL = [(F(0, 0), F(8, 0))]  # on for the whole scene (at most 8 beats)


def frm(b):
    """On from the start of beat b to the end."""
    return [(F(b, 0), F(8, 0))]


def during(a, b):
    """On from the start of beat a to the start of beat b."""
    return [(F(a, 0), F(b, 0))]


def layer(name, lo, hi, mat_, ivs=ALL, wide=False, zmax=0.0):
    return (name, lo, hi, mat_, ivs, wide, zmax)


def glow(m, name, lo, hi, ivs, wide=True):
    """A cyan highlight in front of a band (alpha, so the layers show through)."""
    return layer(name, lo, hi, m["hl_soft"], ivs, wide, 6.0)


def gate(root, m, cx, pre, layers):
    """One gate at cx: its source and drain, then the layers, each its own group switched by its
    intervals. A layer is a slab from z = -240 to its zmax (0: its front on the cut plane)."""
    g = empty(pre, root)
    sd = m["c_nplus"] if pre == "n" else m["c_pplus"]
    for sgn in (-1, 1):
        x = cx + sgn * SD
        box(f"{pre}_sd{sgn}", (x - 70, -90, -240), (x + 70, 6, 0), sd, g)
    for name, lo, hi, mat_, ivs, wide, zmax in layers:
        if isinstance(wide, tuple):
            spans = [(cx - wide[1], cx - wide[0]), (cx + wide[0], cx + wide[1])]
        else:
            r = {False: GH, True: GH + 8, "sheet": SD + 70}.get(wide, wide)
            spans = [(cx - r, cx + r)]
        for k, (x0, x1) in enumerate(spans):
            overlay(g, f"{pre}_{name}{k}", (x0, lo, -240), (x1, hi, zmax), mat_, ivs)
    return g


def stack(m, on, film="hfo2", wfm="tialc", poly=False):
    """The high-k gate, layer by layer from the silicon up. `on[name]` gives a layer's intervals."""
    o = lambda k: on.get(k, ALL)  # noqa: E731
    L = [layer("il", *IL, m["il"], o("il"), True)]
    if film:
        (lo, hi), mat_name = FILM[film]
        L.append(layer("hk", lo, hi, m[mat_name], o("hk"), True))
    if poly:
        L.append(layer("poly", 5.0, 120.0, m["poly"], o("poly")))
    L += [
        layer("wfm", *TIALC, m[wfm], o("wfm")),
        layer("tin", *TIN, m["tin"], o("tin")),
        layer("fill", *FILL, m["c_w"], o("fill")),
    ]
    return L


def gaa(m, on=None):
    """Three nanosheets, the gate in the four gaps between and around them (each gap has an IL,
    HfO2, work-function metal and fill band)."""
    on = on or {}
    L = []
    for k, (lo, hi) in enumerate(GAA_GAPS):
        ivs = on.get(k, ALL)
        L.append(layer(f"g{k}_il", lo, lo + 5, m["il"], ivs))
        L.append(layer(f"g{k}_hk", lo + 5, lo + 23, m["hfo2"], ivs))
        L.append(layer(f"g{k}_wfm", lo + 23, lo + 35, m["tialc"], ivs))
        L.append(layer(f"g{k}_fill", lo + 35, hi, m["c_w"], ivs))
    for i, (lo, hi) in enumerate(GAA_SHEETS):
        L.append(layer(f"sheet{i}", lo, hi, m["sheet"], ALL, "sheet"))
    return L


def base(root, m, layers, pmos=True, whole=False):
    """The silicon, the NMOS gate with `layers`, the PMOS and the contacts; the wiring and bumps
    too for a whole-chip scene."""
    C.silicon(root, m)
    gate(root, m, CX, "n", layers)
    if pmos:
        C.transistor(root, m, PX, False)
    C.contacts(root, m)
    if whole:
        C.wiring(root, m)
        C.bumps(root, m)


def scene(name, beats, poses, body):
    """A fresh Blender file of `beats` beats: body(root, m) draws it, the camera glides through
    `poses` (one per beat), and the GLB is exported."""
    m, root = start(name, beats, page="chip")
    C.mats(m)
    mats(m)
    body(root, m)
    C.glide_camera(root, poses)
    finish(name, page="chip")


def tag(root, text, x, y, ivs):
    label(text, (x, y, 0.0), root, ivs)


def zoom_pose(t, d, pitch=0.05):
    return (t, d, 0.0, pitch)


def name_of(stem):
    return f"{NAME}_{stem}"


def zoom_a(stem="zoom_a"):
    """The layers, from interlayer to fill."""

    def body(root, m):
        L = stack(m, {}) + [
            glow(m, "hl_dielectric", -2.0, 24.0, during(0, 1)),
            glow(m, "hl_metal", 22.0, 42.0, during(1, 2)),
            glow(m, "hl_fill", 40.0, 122.0, during(2, 3)),
        ]
        base(root, m, L)
        tag(root, "IL SiOx ~0.5 nm", CX - 105, 2.5, during(0, 1))
        tag(root, "HfO2 high-k", CX + 105, 14.0, during(0, 1))
        tag(root, "TiAlC(N) work-function", CX - 105, 30.0, during(1, 2))
        tag(root, "TiN glue", CX + 105, 38.0, during(1, 2))
        tag(root, "W fill: gate metal", CX + 105, 90.0, during(2, 3))
        tag(root, "NMOS gate stack", CX, 150.0, during(3, 4))

    scene(name_of(stem), 4, [
        zoom_pose((CX, 30.0, 0.0), 520.0), zoom_pose((CX, 40.0, 0.0), 520.0),
        zoom_pose((CX, 80.0, 0.0), 520.0), zoom_pose((CX, 60.0, 0.0), 560.0),
    ], body)


POLY_OUT = [(F(0, 0), F(2, 0.5))]  # the dummy poly, pulled out half way through beat 2


def zoom_b(stem="zoom_b"):
    """Gate-last: dummy poly, the S/D anneal, poly pull, the stack goes in."""

    def body(root, m):
        L = stack(m, {"hk": frm(3), "wfm": frm(3), "tin": frm(3), "fill": frm(3), "poly": POLY_OUT},
                  poly=True)
        L += [
            layer("ild", 0.0, 120.0, m["ild"], during(1, 4), (GH + 8, GH + 70)),
            layer("anneal", -96.0, 12.0, m["glow"], during(1, 2), (SD - 80, SD + 80), 6.0),
        ]
        base(root, m, L)
        tag(root, "dummy poly", CX + 105, 105.0, during(0, 1))
        tag(root, "S/D anneal ~1000 C", CX - 105, -40.0, during(1, 2))
        tag(root, "ILD fill, polished", CX + 125, 80.0, during(1, 2))
        tag(root, "poly out: trench", CX, 60.0, during(2, 3))
        tag(root, "HfO2 + metal in trench", CX + 105, 14.0, during(3, 4))

    scene(name_of(stem), 4, [zoom_pose((CX, 60.0, 0.0), 520.0)] * 4, body)


def zoom_c(stem="zoom_c"):
    """EOT: thin SiO2 leaks; HfO2 is thick at the same EOT; Intel 45 nm has little leakage."""

    def body(root, m):
        L = stack(m, {"hk": during(0, 1)}, film="sio2") + [
            layer("hk2", *HFO2, m["hfo2"], frm(1), True),
            layer("eot_ref", *EOT_Y, m["ghost"], frm(1), True),
            layer("gate_glow", -2.0, FILL[1] + 6, m["glow"], during(2, 4), True, 6.0),
        ]
        base(root, m, L)
        for dx in (-50.0, 0.0, 50.0):
            s, p = route([(CX + dx, 30.0, FIELD_Z), (CX + dx, -8.0, FIELD_Z)])
            stream_of(root, f"leak{dx:+.0f}", 9, s, p, 40, m["c_dot_out"], 0, 0.20, 0.75, 50)
        tag(root, "SiO2 ~1.2 nm", CX + 105, 11.0, during(0, 1))
        tag(root, "tunnelling", CX - 105, 30.0, during(0, 1))
        tag(root, "HfO2 1.5-2 nm, thick", CX + 105, 14.0, during(1, 2))
        tag(root, "EOT ~1 nm: as SiO2", CX, 178.0, during(1, 4))
        tag(root, "HKMG 45 nm: 10x less leak", CX, 120.0, during(2, 3))
        tag(root, "EOT = t_hk x 3.9 / k", CX, 196.0, during(3, 4))

    scene(name_of(stem), 4, [
        zoom_pose((CX, 50.0, 0.0), 520.0), zoom_pose((CX, 90.0, 0.0), 560.0),
        zoom_pose((CX, 90.0, 0.0), 560.0), zoom_pose((CX, 90.0, 0.0), 560.0),
    ], body)


def zoom_d(stem="zoom_d"):
    """Work-function metals and dipoles: NMOS TiAlC(N), PMOS TiN, a La cap, both gates."""

    def body(root, m):
        Ln = stack(m, {}) + [
            glow(m, "hl_wfm", 22.0, 36.0, during(0, 1)),
            layer("dip", 23.0, 26.0, m["dip"], during(2, 3), False, 6.0),
        ]
        Lp = stack(m, {}, wfm="tin") + [glow(m, "hl_wfm", 22.0, 36.0, during(1, 2))]
        C.silicon(root, m)
        gate(root, m, CX, "n", Ln)
        gate(root, m, PX, "p", Lp)
        C.contacts(root, m)
        tag(root, "TiAlC(N): NMOS metal", CX + 105, 29.0, during(0, 1))
        tag(root, "TiN: PMOS metal", PX + 105, 29.0, during(1, 2))
        tag(root, "La dipole: lower nFET Vt", CX + 105, 25.0, during(2, 3))
        tag(root, "two gates, two Vt", 0.0, 150.0, during(3, 4))

    scene(name_of(stem), 4, [
        zoom_pose((CX, 40.0, 0.0), 520.0), zoom_pose((PX, 40.0, 0.0), 520.0),
        zoom_pose((CX, 40.0, 0.0), 520.0), zoom_pose((0.0, 60.0, 0.0), 1500.0),
    ], body)


def zoom_e(stem="zoom_e"):
    """The stack in a nanosheet gap: wrapped sheets, what fits, Vt varies, the channel."""

    def body(root, m):
        L = gaa(m) + [
            glow(m, "hl_gap1", 54.0, 104.0, during(1, 2), False),
            glow(m, "hl_gap2", 118.0, 168.0, during(2, 3), False),
        ]
        L += [layer(f"chan{i}", lo, hi, m["hl_soft"], during(3, 4), "sheet", 6.0)
              for i, (lo, hi) in enumerate(GAA_SHEETS)]
        base(root, m, L)
        tag(root, "sheets: gate on four sides", CX + 40.0, 80.0, during(0, 1))
        tag(root, "IL + HfO2 + metal fit", CX + 40.0, 70.0, during(1, 2))
        tag(root, "gap ~10 nm: Vt varies", CX + 40.0, 150.0, during(2, 3))
        tag(root, "channel: current in sheets", CX + 40.0, 40.0, during(3, 4))

    scene(name_of(stem), 4, [
        zoom_pose((CX, 111.0, 0.0), 520.0), zoom_pose((CX, 79.0, 0.0), 300.0),
        zoom_pose((CX, 150.0, 0.0), 300.0), zoom_pose((CX, 111.0, 0.0), 520.0),
    ], body)


def sec1(stem="sec1"):
    """What happens: the whole chip with the NMOS bare, then the ALD layers grown in turn."""

    def body(root, m):
        L = stack(m, {"il": frm(1), "hk": frm(1), "wfm": frm(2), "tin": frm(2), "fill": frm(2)}) + [
            layer("nmos_hl", -140.0, 150.0, m["hl"], during(0, 1), 330.0, 14.0),
        ]
        base(root, m, L, whole=True)
        tag(root, "NMOS gate, bare for now", CX, 270.0, during(0, 1))
        tag(root, "ALD: IL, then HfO2", CX + 105, 14.0, during(1, 2))
        tag(root, "ALD: metal, then fill", CX + 105, 80.0, during(2, 3))

    scene(name_of(stem), 3, [WHOLE, zoom_pose((CX, 60.0, 0.0), 520.0),
                             zoom_pose((CX, 60.0, 0.0), 520.0)], body)


def sec4(stem="sec4"):
    """Gate-first versus gate-last: the stack in before the anneal, the poly in for it, then the
    stack after."""

    def body(root, m):
        on = {"hk": during(0, 1) + during(2, 3), "wfm": during(0, 1) + during(2, 3),
              "tin": during(0, 1) + during(2, 3), "fill": during(0, 1) + during(2, 3),
              "poly": during(1, 2)}
        L = stack(m, on, poly=True) + [
            layer("anneal", -96.0, 12.0, m["glow"], during(0, 2), (SD - 80, SD + 80), 6.0),
        ]
        base(root, m, L)
        tag(root, "gate-first: stack in, then ~1000 C", CX + 60, 60.0, during(0, 1))
        tag(root, "gate-last: dummy poly takes heat", CX + 60, 60.0, during(1, 2))
        tag(root, "gate-last: stack in after", CX + 60, 60.0, during(2, 3))

    scene(name_of(stem), 3, [zoom_pose((CX, 40.0, 0.0), 560.0)] * 3, body)


def sec6(stem="sec6"):
    """Threshold tuning in a nanosheet gate: a La cap on one sheet, an Al cap on another."""

    def body(root, m):
        L = gaa(m) + [
            layer("dip_a", 23.0, 26.0, m["dip"], during(0, 1) + during(2, 3), False, 6.0),
            layer("dip_b", 141.0, 144.0, m["dip"], during(1, 3), False, 6.0),
        ]
        base(root, m, L)
        tag(root, "La dipole: lowers nFET Vt", CX + 40.0, 25.0, during(0, 1))
        tag(root, "Al dipole: higher Vt", CX + 40.0, 150.0, during(1, 2))
        tag(root, "one chip, several Vt", CX + 40.0, 100.0, during(2, 3))

    scene(name_of(stem), 3, [
        zoom_pose((CX, 30.0, 0.0), 300.0), zoom_pose((CX, 150.0, 0.0), 300.0),
        zoom_pose((CX, 100.0, 0.0), 400.0),
    ], body)


def sec7(stem="sec7"):
    """By the numbers: the SiO2 limit, the HfO2 EOT, the ALD market."""

    def body(root, m):
        L = stack(m, {"hk": during(0, 1)}, film="sio2") + [
            layer("hk2", *HFO2, m["hfo2"], frm(1), True),
            layer("gate_glow", -2.0, FILL[1] + 6, m["glow"], during(2, 3), True, 6.0),
        ]
        base(root, m, L)
        tag(root, "SiO2 limit ~1.2 nm", CX + 105, 11.0, during(0, 1))
        tag(root, "HfO2 ~1.0 nm EOT", CX + 105, 14.0, during(1, 2))
        tag(root, "ALD market $3.0B (2024)", CX + 105, 80.0, during(2, 3))

    scene(name_of(stem), 3, [zoom_pose((CX, 40.0, 0.0), 520.0), zoom_pose((CX, 40.0, 0.0), 520.0),
                             zoom_pose((CX, 60.0, 0.0), 520.0)], body)


def sec8(stem="sec8"):
    """Who makes it: the ALD films, the metals, then the whole stack."""

    def body(root, m):
        L = stack(m, {}) + [
            glow(m, "hl_ald", -2.0, 24.0, during(0, 1)),
            glow(m, "hl_metal", 22.0, 122.0, during(1, 2)),
            layer("gate_glow", -2.0, FILL[1] + 6, m["glow"], during(2, 3), True, 6.0),
        ]
        base(root, m, L)
        tag(root, "ASM International (ASM.AS)", CX + 105, 14.0, during(0, 1))
        tag(root, "Applied, Lam Research", CX + 105, 80.0, during(1, 2))
        tag(root, "TEL, TSMC, Intel", CX + 105, 100.0, during(2, 3))

    scene(name_of(stem), 3, [zoom_pose((CX, 60.0, 0.0), 520.0)] * 3, body)


def sec9(stem="sec9"):
    """Chokepoints and risks: Vt varies in the gaps, the IL thickness, voids in the fill."""

    def body(root, m):
        L = gaa(m) + [
            glow(m, "hl_gap0", 0.0, 40.0, during(0, 1), False),
            glow(m, "hl_il", 54.0, 59.0, during(1, 2), False),
        ]
        L += [layer(f"chan{i}", lo, hi, m["hl_soft"], during(0, 1), "sheet", 6.0)
              for i, (lo, hi) in enumerate(GAA_SHEETS)]
        base(root, m, L)
        tag(root, "Vt varies in tiny gaps", CX + 40.0, 80.0, during(0, 1))
        tag(root, "0.1 nm of IL moves EOT", CX + 40.0, 56.0, during(1, 2))
        tag(root, "fill voids", CX + 40.0, 96.0, during(2, 3))
        ball_void = ball("void", (CX, 96.0, 0.0), 12.0, m["void"], root, 14)
        show(ball_void, during(2, 3))

    scene(name_of(stem), 3, [zoom_pose((CX, 90.0, 0.0), 360.0), zoom_pose((CX, 60.0, 0.0), 300.0),
                             zoom_pose((CX, 96.0, 0.0), 300.0)], body)


def sec10(stem="sec10"):
    """Sources: the whole chip, a slow pull-back, the source numbers as labels."""

    def body(root, m):
        L = stack(m, {}) + [layer("nmos_hl", -140.0, 150.0, m["hl"], ALL, 330.0, 14.0)]
        base(root, m, L, whole=True)
        tag(root, "sources 1-2: Intel 45 nm", 0.0, 700.0, during(0, 1))
        tag(root, "sources 3-4: HfO2, EOT, gate-last", 0.0, 700.0, during(1, 2))
        tag(root, "sources 5-8: ASM, Lam, Applied", 0.0, 700.0, during(2, 3))

    scene(name_of(stem), 3, [WHOLE, ((0.0, 620.0, 0.0), 7000.0, 0.0, 0.10),
                             ((0.0, 620.0, 0.0), 8000.0, 0.0, 0.10)], body)


SCENES = {
    "zoom_a": zoom_a, "zoom_b": zoom_b, "zoom_c": zoom_c, "zoom_d": zoom_d, "zoom_e": zoom_e,
    "sec1": sec1, "sec2": lambda: zoom_b("sec2"), "sec3": lambda: zoom_a("sec3"), "sec4": sec4,
    "sec5": lambda: zoom_c("sec5"), "sec6": sec6, "sec7": sec7, "sec8": sec8, "sec9": sec9,
    "sec10": sec10,
}


if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None
    if which is None or "overview" in which:
        build()
        finish(NAME, page="chip")
    for key in (SCENES if which is None else which):
        if key != "overview":
            SCENES[key]()
