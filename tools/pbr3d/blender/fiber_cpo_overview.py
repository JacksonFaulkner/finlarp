"""The FIBER CPO node's overview: the co-packaged-optics switch package, in the picture-and-panel
template (docs/diagram-pages.md), built from the detailed parts in fiber_cpo_detail.py.

Run from the repo root (on the worker, or locally):

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_cpo_overview.py

Writes blender/fiber_cpo_overview.blend and assets/fiber_cpo_overview.glb. One beat is 8 s.
The package sits at the origin: switch chip, eight optical engines, fibre to passive connectors, one
engine's cable to a front-panel adapter, and the external laser beside it. Beat 0 adds the rest of the
link (fiber_kit's stations, scaled up and placed so its CPO station falls on this package) as context.
Data and light move as beads riding their paths (wires, traces, fibres), as on the PHOTODIODE page.

Beats (match the seven beats in diagrams_nodes/fiber/cpo/overview.rs):
  0 the whole link, CPO highlighted   the five other stations to the left, the package outlined
  1 the package                       switch chip and eight engines on one substrate
  2 the electrical hop                data beads cross a few mm of copper between chip and engine
  3 bits to light                     laser light rides in; the rings flash; data light leaves into the fibres
  4 the passive connector             the light runs through the connector and the cable to the panel
  5 shared heat                       the chip's heat, reaching the engines beside it
  6 next                              the light leaves the panel on a cable toward the next switch
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, box, empty, label, pivot, rel, show, tube  # noqa: E402
from pbr_kit import flicker  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
from chip_kit import glide_camera  # noqa: E402
import fiber_kit as K  # noqa: E402
import fiber_cpo_detail as D  # noqa: E402
import fiber_cpo_sections as S  # noqa: E402

PAGE = "fiber_cpo"
NAME = "overview"
BEATS = 7
KS = 2.4  # fiber_kit's stations scaled up to this package's size
FRONT = S.FRONT
W = S.W
pose = S.pose
YC = D.FIB_Y + 1.2  # the PM fibres' run height
OUT_X1 = 230.0      # the outgoing cable runs out of frame toward the next switch


def beat(i):
    return [(F(i, 0), F(i + 1, 0))]


def kit_link(m, root):
    """Beat 0's context: fiber_kit's other five stations, scaled by KS and shifted so the kit's CPO
    station lands on this package. Nested empties: show() owns the outer one's scale."""
    outer = empty("link_context", root)
    show(outer, beat(0))
    inner = empty("link_scaled", outer)
    inner.location = P(-K.CPO_X * KS, 7.0 * KS, 0.0)
    inner.scale = (KS, KS, KS)
    km = K.materials()
    K.trace(km, inner)
    K.dsp(km, inner)
    K.laser(km, inner)
    K.fibre(km, inner)
    K.photodiode(km, inner)
    K.module(km, inner)
    return outer


def kx(x):
    """A kit x coordinate in this scene."""
    return (x - K.CPO_X) * KS


def scene(m, root):
    """Everything but the camera and the tags. Returns the package dict."""
    box("board_left", (-660.0, -3.0, -75.0), (-75.0, 0.0, 75.0), m["board"], root)
    D.board(m, root, x1=82.0)
    pk = D.package(m, root)
    oe = pk["oes"][FRONT]
    D.mate(m, oe, 52.0)
    S.panel(m, root, 76.0, gaps=[(2.0, 15.0), (-27.0, -11.0)])
    S.els(m, root, 66.0, -19.0, 62.5, pm=False)
    tube("cable_out", (79.0, D.FIB_Y, 8.5), (OUT_X1, D.FIB_Y, 8.5), 1.6, m["aqua"], root, 16)
    kit_link(m, root)
    # Beat 0: the package outlined in the whole link.
    S.halo(m, root, (-60.0, -0.4, -60.0), (60.0, 7.0, 60.0), beat(0))

    # The polarisation-maintaining fibres: arched, segmented, from the laser's port to the cable
    # connector's two laser lanes; they glow with the laser's steady light.
    lanes = []
    for s, zl in zip((-1, 1), S.LZ):
        a = (64.5, YC, -19.0 + 3.0 * s)
        b = (62.5, YC, zl)
        pts = D.arch(a, b, 7.0, 10)
        D.wire(f"pm_{zl}", pts, 0.32, m["cladding"], root)
        D.wire(f"pmc_{zl}", pts, 0.18, m["cw"], root)
        tube(f"pm_drop_{zl}", b, (62.5, D.FIB_Y, zl), 0.32, m["cladding"], root, 10)
        lanes.append(pts + [(62.5, D.FIB_Y, zl), (31.0, D.FIB_Y, zl), (30.9, D.PIC_Y1 + 0.12, zl),
                            (23.0, D.PIC_Y1 + 0.12, zl)])
    D.lit_lanes(m, oe, D.LASER, 7.0, D.FERRULE_U + 3.0)

    # Beat 2: data beads on the FRONT engine's traces: out to the EIC on the lower lanes, back to the
    # chip on the upper.
    for i, v in enumerate(D.LANES):
        a, b = (-12.6, -5.8) if v < 0 else (-5.8, -12.6)
        D.ride(oe["g"], f"hop_{v}", [(a, D.SUB_Y1 + 0.2, v), (b, D.SUB_Y1 + 0.2, v)], 8, 0.3, m["elec"],
               2, 0.026 * i, 0.85, 40)

    # Beat 3: laser light rides in on the PM fibres; the rings flash; data light leaves into the fibres.
    for k, pts in enumerate(lanes):
        D.ride(root, f"cw_{k}", pts, 9, 0.38, m["cw"], 3, 0.0, 0.85, 70)
    wg = empty("wg_lit", oe["g"])
    show(wg, [(F(3, 0), F(5, 0))])
    for v in D.LASER:
        box(f"wgl_{v}", (-1.2, D.PIC_Y1, v - 0.09), (7.0, D.PIC_Y1 + 0.05, v + 0.09), m["cw"], wg)
    box("bus_l", (-1.25, D.PIC_Y1, -3.6), (-0.95, D.PIC_Y1 + 0.05, 3.6), m["cw"], wg)
    on = empty("rings_on", oe["g"])
    show(on, beat(3))
    for i, v in enumerate(D.TX):
        r = D.ring(f"ron_{v}", (1.2 + 1.1 * i, D.PIC_Y1 + 0.04, v + 0.45), 0.36, m["ring_on"], on, 0.1)
        flicker(r, F(3, 0), F(4, 0), amps=(1.0, 0.2, 1.0, 1.0, 0.2, 1.0), every=5 + i)
    for i, v in enumerate(D.TX):
        x0 = 1.2 + 1.1 * i
        D.ride(oe["g"], f"mod_{v}", [(x0, D.PIC_Y1 + 0.12, v), (7.0, D.PIC_Y1 + 0.12, v), (7.2, D.FIB_Y, v),
                                     (22.0, D.FIB_Y, v)], 8, 0.32, m["light"], 3, 0.0, 0.85, 50)

    # Beat 4: the light runs along the fibres, through the connector and the cable to the panel.
    for v in D.TX:
        D.ride(oe["g"], f"conn_{v}", [(10.0, D.FIB_Y, v), (16.0, D.FIB_Y + 0.5, v), (28.0, D.FIB_Y + 0.5, v),
                                      (28.2, D.FIB_Y, v), (D.FERRULE_U + 11.0, D.FIB_Y, v),
                                      (D.FERRULE_U + 11.5, D.FIB_Y + 0.6, v), (52.0, D.FIB_Y + 0.6, v)],
               8, 0.4, m["light"], 4, 0.0, 0.85, 60)

    # Beat 5: the chip's heat, reaching the engines.
    hot = empty("asic_heat", root)
    show(hot, beat(5))
    at = (0.0, 4.0, 0.0)
    pv = pivot("heat_pulse", at, hot)
    box("heat_asic", rel(at, (-13.6, 3.2, -13.6)), rel(at, (13.6, 8.0, 13.6)), m["heat"], pv)
    flicker(pv, F(5, 0), F(6, 0), every=8)
    for (s_, lat), d in pk["oes"].items():
        h = empty(f"oe_heat_{s_}_{lat}", d["g"])
        show(h, beat(5))
        box(f"oe_heat_box_{s_}_{lat}", (-7.3, 3.0, -4.8), (7.3, 5.6, 4.8), m["warm"], h)

    # Beat 6: the light leaves the panel on the cable, toward the next switch.
    D.ride(root, "next", [(79.0, D.FIB_Y + 1.7, 8.5), (OUT_X1, D.FIB_Y + 1.7, 8.5)], 10, 0.9, m["light"],
           6, 0.0, 0.85, 70)
    return pk


TAGS = {
    0: [("PAM4 DSP", (kx(K.DSP_X), 24.0, 0.0)),
        ("LASER", (kx(K.LASER_X), 18.0, 0.0)),
        ("OPTICAL FIBER", (kx(80.0), 6.0, 0.0)),
        ("PHOTODIODE", (kx(K.PD_X), 18.0, 0.0)),
        ("TRANSCEIVER", (kx(K.MOD_X), 48.0, 0.0)),
        ("CPO", (0.0, 7.0, 40.0))],
    1: [("SWITCH CHIP", (-4.0, 4.05, 2.0)),
        ("8 OPTICAL ENGINES", W(-4.0, 4.4, 0.0)),
        ("ONE SUBSTRATE", (-24.0, 2.8, 39.0))],
    2: [("SERDES EDGE", (12.0, 4.05, 4.0)),
        ("A FEW MM OF COPPER", W(-9.5, 2.95, -1.5)),
        ("ELECTRONIC CHIP", W(-4.0, 4.4, 1.0))],
    3: [("LASER LIGHT IN", W(4.0, D.PIC_Y1 + 0.05, -3.5)),
        ("RING MODULATORS", W(2.3, D.PIC_Y1 + 0.05, -1.05)),
        ("INTO THE FIBRE ARRAY", W(10.0, 4.05, 0.0))],
    4: [("PASSIVE CONNECTOR", W(30.0, 5.2, -1.0)),
        ("NO ELECTRONICS INSIDE", W(32.0, 2.0, -4.8)),
        ("CABLE TO THE PANEL", W(48.0, D.FIB_Y + 0.45, 0.0))],
    5: [("CHIP HEAT", (0.0, 8.0, 0.0)),
        ("REACHES THE ENGINES", W(0.0, 5.6, 0.0))],
    6: [("FRONT PANEL", (77.0, 14.0, -2.0)),
        ("ON TO THE NEXT SWITCH", (150.0, D.FIB_Y + 1.6, 8.5))],
}

POSES = [
    pose((-270.0, 0.0, -110.0), 560.0, 0.55, 0.55),
    pose((0.0, 3.0, 4.0), 118.0, 0.40, 0.72),
    pose(W(-7.0, 3.2, 0.0), 20.0, 0.10, 1.05),
    pose(W(6.0, 3.6, 0.0), 26.0, 0.30, 0.85),
    pose(W(34.0, 3.5, 0.0), 40.0, 0.45, 0.55),
    pose((4.0, 3.5, 4.0), 90.0, 0.40, 0.75),
    pose((100.0, 4.0, 4.0), 150.0, 0.30, 0.55),
]


def build(tags=True, poses=None, cam=None):
    """The overview scene. `tags=False` leaves the tags off; `cam(root, poses)` replaces the camera."""
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = D.materials()
    D.CLIP = None
    scene(m, root)
    if tags:
        for i, lst in TAGS.items():
            for text, at in lst:
                label(text, at, root, beat(i))
    poses = poses or POSES
    if cam is None:
        glide_camera(root, poses, glide=0.25)
    else:
        cam(root, poses)
    root.scale = (S.SCALE, S.SCALE, S.SCALE)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
