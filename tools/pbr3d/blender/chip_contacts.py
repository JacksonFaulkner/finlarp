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
e new metals. Sections (3 to 4 beats each): 1 what happens ... 10 sources.

The silicide caps and the liner-and-tungsten plugs are built here (chip_kit's contacts are plain
plugs); the rest of the chip is chip_kit's, unchanged.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_zooms import finish, start  # noqa: E402
import chip_kit as C  # noqa: E402
from chip_kit import F, box, empty, label, mat, route, stream_of, tube  # noqa: E402

BEATS = 6
PLUG_TOP = 404.0  # up inside the thin M1 wire (its centre is at level_y("thin", 0) = 410)
SIL = (6.0, 30.0)  # the silicide cap sits on the top of the source and drain blocks
PLUG_R, CORE_R = 28.0, 22.0  # the plug is the liner (outer ring) around a tungsten core
SRC_X, DRN_X = C.NMOS_X - C.SD, C.NMOS_X + C.SD  # the NMOS source is outside, the drain is inside

WHOLE = C.WHOLE
PLUGS = ((0.0, 240.0, 0.0), 3500.0, 0.0, 0.10)
ZOOM = ((C.NMOS_X, 120.0, 0.0), 1100.0, 0.0, 0.08)
SQUEEZE = ((C.NMOS_X, 230.0, 0.0), 1700.0, 0.0, 0.08)
POSES = [WHOLE, PLUGS, ZOOM, SQUEEZE, ZOOM, WHOLE]


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


def base(name, beats, lit_thin=(), nmos_lit=()):
    """The whole chip, built the same for every CONTACTS scene. `lit_thin` and `nmos_lit` are
    intervals that light the M1 wires and the NMOS channel and gate."""
    m, root = start(name, beats, page="chip")
    C.mats(m)
    extra_mats(m)
    C.silicon(root, m)
    C.transistor(root, m, C.NMOS_X, True, lit=nmos_lit)
    C.transistor(root, m, C.PMOS_X, False)
    contacts(root, m)
    C.wiring(root, m, lit_thin=lit_thin)
    C.bumps(root, m)
    return m, root


def build(name="contacts", poses=POSES):
    m, root = base(name, BEATS)

    whole = [(F(0, 0), F(1, 0)), (F(5, 0), F(6, 0))]

    # beats 0 and 1: the contact layer, the band between silicon and thin metal, lit over both
    for cx in (C.NMOS_X, C.PMOS_X):
        C.overlay(root, f"lit_contacts{cx:.0f}", (cx - C.SD - 80, -10, -110), (cx + C.SD + 80, PLUG_TOP + 8, -10),
                  m["k_lit"], [(F(0, 0), F(2, 0))])

    # beats 2 and 4: the silicide lights when it is the one doing the work
    for cx in (C.NMOS_X, C.PMOS_X):
        for x in (cx - C.SD, cx + C.SD):
            C.overlay(root, f"lit_sil{x:.0f}", (x - 84, SIL[0] - 6, -116), (x + 84, SIL[1] + 10, -4),
                      m["k_sil_on"], [(F(2, 0), F(3, 0)), (F(4, 0), F(5, 0))])

    # beat 3: current from M1 down the drain plug, the narrow column, into the silicide
    s, p = route([(DRN_X, PLUG_TOP, -60.0), (DRN_X, SIL[0] + 10, -60.0)])
    stream_of(root, "squeeze", 9, s, p, 20, m["c_dot_sig"], 3, 0.05, 0.60, 70)
    # beat 4: the same run down the source plug, across the silicide
    s, p = route([(SRC_X, PLUG_TOP, -60.0), (SRC_X, SIL[0] + 10, -60.0)])
    stream_of(root, "cross", 9, s, p, 20, m["c_dot_sig"], 4, 0.05, 0.60, 70)

    label("contacts", (1150.0, 230.0, 0), root, whole)
    b1 = [(F(1, 0), F(2, 0))]
    label("source plug", (SRC_X, 150.0, 0), root, b1)
    label("gate plug", (C.NMOS_X, 300.0, 0), root, b1)
    label("drain plug", (DRN_X, 150.0, 0), root, b1)
    label("thin metal M1", (0.0, 450.0, 0), root, b1)
    b2 = [(F(2, 0), F(3, 0))]
    label("silicide, source", (SRC_X, 60.0, 0), root, b2)
    label("silicide, drain", (DRN_X, 60.0, 0), root, b2)
    label("n+ source and drain", (C.NMOS_X, -150.0, 0), root, b2)
    b3 = [(F(3, 0), F(4, 0))]
    label("small plug: current squeezes", (-820.0, 250.0, 0), root, b3)
    b4 = [(F(4, 0), F(5, 0))]
    label("silicide: lower barrier", (SRC_X, 60.0, 0), root, b4)
    label("contact resistance", (C.NMOS_X, 300.0, 0), root, b4)

    C.glide_camera(root, poses)


# ---- the zoom-ins and sections: one spec per scene, built by build_scene -----------------------
# A spec is a dict: beats, poses (one per beat), thin / nmos (beats that light M1 or the NMOS),
# lit (tag, lo, hi, material, beats), streams (tag, path, beat, dot size, material) and
# labels (text, at, beat). Beat numbers are indexes from 0.


def iv(*bs):
    return [(F(b, 0), F(b + 1, 0)) for b in bs]


def sil_zone(x):
    return (x - 84, SIL[0] - 6, -116), (x + 84, SIL[1] + 10, -4)


def plug_zone(x):
    return (x - 44, SIL[1] - 6, -104), (x + 44, PLUG_TOP + 8, -16)


def gate_zone():
    return (C.NMOS_X - 44, 116, -104), (C.NMOS_X + 44, PLUG_TOP + 8, -16)


def contacts_zone(cx):
    return (cx - C.SD - 80, -10, -110), (cx + C.SD + 80, PLUG_TOP + 8, -10)


def sac_zone():
    return (C.NMOS_X - C.GATE_HALF - 8, 120, -250), (C.NMOS_X + C.GATE_HALF + 8, 146, 6)


def down(x):
    return [(x, PLUG_TOP, -60.0), (x, SIL[0] + 10, -60.0)]


def up(x):
    return [(x, SIL[1] + 4, -60.0), (x, PLUG_TOP - 10, -60.0)]


def pose(target, dist, pitch=0.08):
    return (target, dist, 0.0, pitch)


NM_SIL = (C.NMOS_X, 60.0, 0.0)
NM_PLUG = (C.NMOS_X, 200.0, 0.0)
NM_M1 = (C.NMOS_X, 400.0, 0.0)
NM_GATE = (C.NMOS_X, 200.0, 0.0)
DRN_TOP = (DRN_X, 230.0, 0.0)
DRN_LOW = (DRN_X, 60.0, 0.0)
ROW = (0.0, 400.0, 0.0)
M1_OVER = (C.NMOS_X + 100.0, 430.0, 0.0)
PULL = (0.0, 620.0, 0.0)
PULL_WIDE = ((0.0, 620.0, 0.0), 6400.0, 0.0, 0.10)
WIDE = ((0.0, 620.0, 0.0), 5800.0, 0.0, 0.10)

SCENES = {
    # a: the contact module, silicide to M1
    "zoom_a": dict(
        beats=3,
        poses=[pose(NM_SIL, 1000.0), pose(NM_PLUG, 1000.0), pose(NM_M1, 950.0, 0.06)],
        thin=[2],
        lit=[("sil_src", *sil_zone(SRC_X), "k_sil_on", [0]), ("sil_drn", *sil_zone(DRN_X), "k_sil_on", [0]),
             ("plug_src", *plug_zone(SRC_X), "k_lit", [1]), ("plug_drn", *plug_zone(DRN_X), "k_lit", [1]),
             ("plug_gate", *gate_zone(), "k_lit", [1])],
        labels=[("silicide, source", (SRC_X, 60.0, 0.0), 0), ("silicide, drain", (DRN_X, 60.0, 0.0), 0),
                ("liner + tungsten", (DRN_X + 60.0, 250.0, 0.0), 1), ("M1 over the plugs", (C.NMOS_X, 470.0, 0.0), 2)],
    ),
    # b: contact types, trench, gate, selective W
    "zoom_b": dict(
        beats=3,
        poses=[pose(NM_SIL, 1000.0), pose(NM_GATE, 900.0), pose(DRN_TOP, 900.0)],
        lit=[("trench_bar", (SRC_X - 70, 28.0, -250.0), (DRN_X + 70, 64.0, -10.0), "k_wcore", [0]),
             ("gate_plug", *gate_zone(), "k_lit", [1]), ("drain_plug", *plug_zone(DRN_X), "k_lit", [2])],
        streams=[("fill", up(DRN_X), 2, 20, "c_dot_sig")],
        labels=[("trench: one bar on S and D", (C.NMOS_X, 120.0, 0.0), 0), ("gate plug", (C.NMOS_X, 300.0, 0.0), 1),
                ("bottom-up W, no seam", (DRN_X + 60.0, 300.0, 0.0), 2),
                ("Applied claim: >40% lower R", (DRN_X + 60.0, 180.0, 0.0), 2)],
    ),
    # c: SAC cap and COAG, then the smaller cells
    "zoom_c": dict(
        beats=3,
        poses=[pose((C.NMOS_X, 130.0, 0.0), 800.0), pose(NM_GATE, 900.0), WIDE],
        nmos=[1],
        lit=[("sac_cap", *sac_zone(), "k_cap", [0]), ("gate_plug", *gate_zone(), "k_lit", [1]),
             ("contacts_n", *contacts_zone(C.NMOS_X), "k_lit", [2]), ("contacts_p", *contacts_zone(C.PMOS_X), "k_lit", [2])],
        labels=[("SiN cap on the gate", (C.NMOS_X + 180.0, 150.0, 0.0), 0),
                ("contact over the channel", (C.NMOS_X, 300.0, 0.0), 1),
                ("cell ~10% shorter (Intel)", (0.0, 700.0, 0.0), 2)],
    ),
    # d: contact resistance, the silicide, the liner, the barrier
    "zoom_d": dict(
        beats=3,
        poses=[pose((SRC_X, 60.0, 0.0), 900.0), pose(DRN_TOP, 800.0), pose(DRN_LOW, 800.0)],
        lit=[("sil_src", *sil_zone(SRC_X), "k_sil_on", [0]), ("plug_drn", *plug_zone(DRN_X), "k_lit", [1]),
             ("sil_drn", *sil_zone(DRN_X), "k_sil_on", [2])],
        streams=[("squeeze", down(DRN_X), 1, 20, "c_dot_sig"), ("cross", down(DRN_X), 2, 20, "c_dot_sig")],
        labels=[("rho_c / A climbs", (SRC_X - 40.0, 170.0, 0.0), 0), ("liner: a few nm a side", (DRN_X + 60.0, 300.0, 0.0), 1),
                ("barrier 0.7 -> 0.34 eV", (DRN_X + 60.0, 110.0, 0.0), 2)],
    ),
    # e: new metals, tungsten, cobalt, Co / Ru / Mo
    "zoom_e": dict(
        beats=3,
        poses=[pose(DRN_TOP, 900.0), pose(NM_M1, 1100.0, 0.06), pose(ROW, 2600.0, 0.08)],
        thin=[1, 2],
        lit=[("w_src", *plug_zone(SRC_X), "k_lit", [0]), ("w_drn", *plug_zone(DRN_X), "k_lit", [0]),
             ("w_gate", *gate_zone(), "k_lit", [0])],
        labels=[("W: 19.1 nm mean free path", (DRN_X + 60.0, 260.0, 0.0), 0),
                ("cobalt, Intel 10 nm (2017)", (C.NMOS_X, 470.0, 0.0), 1),
                ("Ru ~7.1, Mo ~5.3 uOhm-cm", (C.NMOS_X, 470.0, 0.0), 2)],
    ),
    # sections 1-10, in the page's order
    "sec1": dict(  # what happens: the contact layer, then the plugs, then M1
        beats=3,
        poses=[WIDE, pose(NM_PLUG, 1100.0), pose(NM_M1, 1000.0)],
        lit=[("contacts_n", *contacts_zone(C.NMOS_X), "k_lit", [0]), ("contacts_p", *contacts_zone(C.PMOS_X), "k_lit", [0]),
             ("plug_src", *plug_zone(SRC_X), "k_lit", [1]), ("plug_drn", *plug_zone(DRN_X), "k_lit", [1]),
             ("plug_gate", *gate_zone(), "k_lit", [1])],
        thin=[2],
        labels=[("contacts", (1150.0, 230.0, 0.0), 0), ("W plugs", (DRN_X + 60.0, 250.0, 0.0), 1),
                ("M1 over the plugs", (C.NMOS_X, 470.0, 0.0), 2)],
    ),
    "sec2": dict(  # from M1 down to silicon: M1, the gate cap and plugs, the silicide
        beats=3,
        poses=[pose(M1_OVER, 1000.0), pose(NM_PLUG, 1000.0), pose(NM_SIL, 1000.0)],
        thin=[0],
        lit=[("sac_cap", *sac_zone(), "k_cap", [1]), ("plug_src", *plug_zone(SRC_X), "k_lit", [1]),
             ("plug_drn", *plug_zone(DRN_X), "k_lit", [1]), ("sil_src", *sil_zone(SRC_X), "k_sil_on", [2]),
             ("sil_drn", *sil_zone(DRN_X), "k_sil_on", [2])],
        labels=[("M1 pitch 30-40 nm", (C.NMOS_X, 470.0, 0.0), 0), ("SiN cap, W plugs", (C.NMOS_X + 180.0, 250.0, 0.0), 1),
                ("NiSi on the epi", (DRN_X + 60.0, 60.0, 0.0), 2)],
    ),
    "sec3": dict(  # contact types, then the tricks, then selective W and the new metals
        beats=3,
        poses=[pose(NM_SIL, 1100.0), pose(NM_GATE, 1000.0), pose(DRN_TOP, 900.0)],
        nmos=[1],
        lit=[("trench_bar", (SRC_X - 70, 28.0, -250.0), (DRN_X + 70, 64.0, -10.0), "k_wcore", [0]),
             ("gate_plug", *gate_zone(), "k_lit", [0]), ("sac_cap", *sac_zone(), "k_cap", [1]),
             ("contacts_n", *contacts_zone(C.NMOS_X), "k_lit", [2])],
        streams=[("fill", up(DRN_X), 2, 20, "c_dot_sig")],
        labels=[("trench and gate contacts", (C.NMOS_X, 120.0, 0.0), 0), ("COAG, SAC cap", (C.NMOS_X + 180.0, 150.0, 0.0), 1),
                ("selective W", (DRN_X + 60.0, 300.0, 0.0), 2)],
    ),
    "sec4": dict(  # why contact resistance is the bottleneck: the path, the narrow plug, the liner, the barrier
        beats=4,
        poses=[WIDE, pose(DRN_TOP, 1000.0), pose(DRN_TOP, 800.0), pose(DRN_LOW, 900.0)],
        lit=[("plug_drn", *plug_zone(DRN_X), "k_lit", [2]), ("sil_src", *sil_zone(SRC_X), "k_sil_on", [3]),
             ("sil_drn", *sil_zone(DRN_X), "k_sil_on", [3])],
        streams=[("path", down(DRN_X), 0, 46, "c_dot_sig"), ("squeeze", down(DRN_X), 1, 20, "c_dot_sig"),
                 ("cross", down(DRN_X), 3, 20, "c_dot_sig")],
        labels=[("contact R in series", (DRN_X + 200.0, 330.0, 0.0), 0), ("plug 15-20 nm wide", (DRN_X + 80.0, 250.0, 0.0), 1),
                ("liner: a few nm a side", (DRN_X + 80.0, 300.0, 0.0), 2), ("barrier: 0.7 -> 0.34 eV", (DRN_X + 60.0, 110.0, 0.0), 3)],
    ),
    "sec5": dict(  # by the numbers: the mean free path, the barriers, rho_c, the claims
        beats=4,
        poses=[pose(DRN_TOP, 900.0), pose(DRN_LOW, 800.0), pose(NM_PLUG, 1100.0), WIDE],
        lit=[("plug_drn", *plug_zone(DRN_X), "k_lit", [0]), ("sil_src", *sil_zone(SRC_X), "k_sil_on", [1]),
             ("sil_drn", *sil_zone(DRN_X), "k_sil_on", [1]), ("plug_src", *plug_zone(SRC_X), "k_lit", [2]),
             ("plug_gate", *gate_zone(), "k_lit", [2]), ("contacts_n", *contacts_zone(C.NMOS_X), "k_lit", [3]),
             ("contacts_p", *contacts_zone(C.PMOS_X), "k_lit", [3])],
        streams=[("squeeze", down(DRN_X), 0, 20, "c_dot_sig")],
        labels=[("W mean free path 19.1 nm", (DRN_X + 80.0, 300.0, 0.0), 0), ("NiSi 0.65-0.7 eV", (DRN_X + 60.0, 60.0, 0.0), 1),
                ("rho_c ~3e-9 to 1e-8 ohm-cm2", (C.NMOS_X, 300.0, 0.0), 2), ("claims, not equal tests", (1150.0, 230.0, 0.0), 3)],
    ),
    "sec6": dict(  # Applied Materials: the revenue, the segments, the contact metals
        beats=3,
        poses=[pose(M1_OVER, 1000.0), WIDE, pose(NM_PLUG, 1100.0)],
        thin=[0, 1],
        lit=[("plug_src", *plug_zone(SRC_X), "k_lit", [2]), ("plug_drn", *plug_zone(DRN_X), "k_lit", [2])],
        labels=[("AMAT FY2025: $28.37B", (C.NMOS_X, 470.0, 0.0), 0), ("Semi Systems: $20.80B", (1150.0, 230.0, 0.0), 1),
                ("Endura PVD/CVD/ALD", (DRN_X + 60.0, 250.0, 0.0), 2)],
    ),
    "sec7": dict(  # the new metals: tungsten, cobalt, then Co / Ru / Mo
        beats=3,
        poses=[pose(DRN_TOP, 900.0), pose(NM_M1, 1100.0, 0.06), pose(ROW, 2600.0)],
        thin=[1, 2],
        lit=[("w_src", *plug_zone(SRC_X), "k_lit", [0]), ("w_drn", *plug_zone(DRN_X), "k_lit", [0]),
             ("w_gate", *gate_zone(), "k_lit", [0])],
        labels=[("tungsten: 19.1 nm mfp", (DRN_X + 60.0, 260.0, 0.0), 0), ("cobalt: Intel 10 nm", (C.NMOS_X, 470.0, 0.0), 1),
                ("Ru, Mo: less barrier", (C.NMOS_X, 470.0, 0.0), 2)],
    ),
    "sec8": dict(  # who makes it: the tool makers, the scheme designers, the buyers and EDA
        beats=3,
        poses=[pose(M1_OVER, 1000.0), WIDE, PULL_WIDE],
        thin=[0],
        lit=[("contacts_n", *contacts_zone(C.NMOS_X), "k_lit", [1]), ("contacts_p", *contacts_zone(C.PMOS_X), "k_lit", [1])],
        labels=[("Endura; ALTUS", (C.NMOS_X, 470.0, 0.0), 0), ("TSMC, Intel: contact scheme", (1150.0, 230.0, 0.0), 1),
                ("Samsung, SK hynix, Micron", (-1100.0, 1000.0, 0.0), 2)],
    ),
    "sec9": dict(  # chokepoints and risks: new tools, barrierless fill, contact RC
        beats=3,
        poses=[pose(NM_M1, 1000.0), pose(DRN_TOP, 800.0), WIDE],
        thin=[0],
        lit=[("plug_drn", *plug_zone(DRN_X), "k_lit", [1]), ("contacts_n", *contacts_zone(C.NMOS_X), "k_lit", [2]),
             ("contacts_p", *contacts_zone(C.PMOS_X), "k_lit", [2])],
        labels=[("new tools, qualification", (C.NMOS_X, 470.0, 0.0), 0), ("adhesion, diffusion risk", (DRN_X + 60.0, 250.0, 0.0), 1),
                ("contact RC erodes gains", (1150.0, 230.0, 0.0), 2)],
    ),
    "sec10": dict(  # sources: the whole chip, a slow pull-back
        beats=3,
        poses=[WIDE, PULL_WIDE, ((0.0, 620.0, 0.0), 7200.0, 0.0, 0.12)],
        labels=[("sources 1-3", (-1100.0, 1000.0, 0.0), 0), ("sources 4-6", (-1100.0, 1000.0, 0.0), 1),
                ("sources 7-9", (-1100.0, 1000.0, 0.0), 2)],
    ),
}


def build_scene(name, spec):
    beats = spec["beats"]
    m, root = base(name, beats, lit_thin=iv(*spec.get("thin", ())), nmos_lit=iv(*spec.get("nmos", ())))
    for tag, lo, hi, mk, bs in spec.get("lit", ()):
        C.overlay(root, tag, lo, hi, m[mk], iv(*bs))
    for tag, pts, b, size, mk in spec.get("streams", ()):
        s, p = route(pts)
        stream_of(root, tag, 9, s, p, size, m[mk], b, 0.05, 0.60, 70)
    for text, at, b in spec.get("labels", ()):
        label(text, at, root, iv(b))
    C.glide_camera(root, spec["poses"])


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = argv[0] if argv else "overview"
    if name == "overview":
        build()
        finish("contacts", page="chip")
    else:
        build_scene(name, SCENES[name])
        finish("contacts_" + name, page="chip")
