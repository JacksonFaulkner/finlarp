"""The FIBER CPO node's nine numbered sections, in the picture-and-panel template (docs/diagram-pages.md).
Section N illustrates heading N of tui/src/screens/diagrams_pages/FIB_CPO.txt; three beats each.

Run from the repo root (locally, or through bake_queue.py):

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_cpo_sections.py -- <n>

<n> is 1..9. Writes blender/fiber_cpo_section_<n>.blend and assets/fiber_cpo_section_<n>.glb.
One beat is 8 s. The parts come from fiber_cpo_detail.py: a switch chip in the middle of a layered
substrate, eight optical engines around it (photonic chip + electronic chip + fibre array in
V-grooves), fibres out to passive connectors, a cable to the front panel and an external laser
module beside it. The camera glides to a new pose each beat (chip_kit.glide_camera), framed on what
that beat adds. The beats match diagrams_nodes/fiber/cpo/sections.rs:

  1 what happens        pluggables at the end of long traces; engines on the package; the external laser
  2 the parts           the package and its engines; the engine's ring, photodiode, chips; laser and panel
  3 a bit's path        SerDes to the EIC; the ring imprints laser light; out to the panel and back in
  4 why: the copper     200G over a long trace needs a DSP; millimetres instead; ~25 W vs ~9 W per port
  5 inside the engine   the EIC stacked on the PIC (cut open); rings modulate; heat and heater control
  6 lasers stay pluggable  the external laser at the panel; it slides out and back; two lasers inside
  7 the switches        a CPO switch package; a panel of fibre ports; liquid cooled, ~100 Tb/s
  8 who makes it        switch and chips; lasers; fibre and connectors, each highlighted with its makers
  9 chokepoints         a failed engine; fibre attach; optics tied to one vendor's package
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, box, empty, fly, label, pivot, rel, show, tube  # noqa: E402
from sand_zooms import finish, start, stream_of  # noqa: E402
from pbr_kit import flicker  # noqa: E402
from chip_kit import glide_camera  # noqa: E402
import fiber_cpo_detail as D  # noqa: E402

PAGE = "fiber_cpo"
BEATS = 3
FRONT = ("+x", 8.5)  # the engine most sections close in on: +x side, nearer the camera


def upto(i, j):
    """Beats i through j, inclusive, as one interval."""
    return [(F(i, 0), F(j + 1, 0))]


def begin(n):
    D.CLIP = None
    _, root = start(f"section_{n}", beats=BEATS, page=PAGE)
    return D.materials(), root


def pose(t, span, yaw=0.45, pitch=0.6):
    """A camera pose that fits about `span` mm across the left pane (visible height ~0.53 x distance)."""
    return (t, span / 0.53, yaw, pitch)


SCALE = 5.0  # the renderer's near plane is 40 units: the root is scaled up so close-ups stay past it


def cam(root, poses):
    glide_camera(root, poses, glide=0.25)
    root.scale = (SCALE, SCALE, SCALE)


def W(u, y, v, eng=FRONT, dx=0.0, dz=0.0):
    """A point in an engine's frame, in world coordinates (plus a package offset)."""
    x, y2, z = D.oe_world(eng[0], eng[1], u, y, v)
    return (x + dx, y2, z + dz)


def tags(root, items):
    for i, lst in items.items():
        for text, at in lst:
            label(text, at, root, upto(i, i))


def group(parent, name, intervals):
    g = empty(name, parent)
    show(g, intervals)
    return g


def panel(m, parent, x, z0=-30.0, z1=22.0, h=14.0, gaps=()):
    """A steel front panel standing on the board's edge at x, with windows at the z ranges in `gaps`."""
    edges = [z0] + [z for gap in gaps for z in gap] + [z1]
    for i in range(0, len(edges), 2):
        box(f"panel_{x}_{i}", (x, -3.0, edges[i]), (x + 2.0, h, edges[i + 1]), m["steel"], parent)
    for a, b in gaps:
        box(f"panel_top_{x}_{a}", (x, 11.0, a), (x + 2.0, h, b), m["steel"], parent)


WHOLE = pose((0.0, 3.0, 4.0), 118.0, 0.40, 0.72)



# ---- shared scenes ------------------------------------------------------------------------------

ZP, ZC = -95.0, 62.0  # the pluggable row (back) and the CPO row (front), for sections 1 and 4
PX = 160.0            # their front panel
LZ = (5.0, 12.0)      # world z of FRONT's two laser lanes


def pluggable_row(m, root, data_beat=0):
    g = empty("pluggable_row", root)
    # A conventional switch package: substrate, die, lid, no optics on it.
    box("p_sub", (-30.0, 0.8, ZP - 30.0), (30.0, 2.8, ZP + 30.0), m["buildup"], g)
    box("p_lid", (-24.0, 2.8, ZP - 24.0), (24.0, 5.5, ZP + 24.0), m["steel"], g)
    box("p_lid_top", (-18.0, 5.5, ZP - 18.0), (18.0, 6.0, ZP + 18.0), m["steel"], g)
    mz = (-21.0, -7.0, 7.0, 21.0)
    for i, dz in enumerate(mz):
        z = ZP + dz
        for s in (-1.2, 1.2):
            box(f"p_tr_{i}_{s}", (30.0, 0.0, z + s - 0.35), (PX - 30.0, 0.06, z + s + 0.35), m["copper"], g)
        box(f"p_cage_{i}", (PX - 32.0, 0.0, z - 6.5), (PX, 10.0, z + 6.5), m["cage"], g)
        front = i == len(mz) - 1
        zf = z if front else z + 6.0  # the front module is cut open down its middle
        box(f"p_mod_{i}", (PX - 30.0, 0.5, z - 6.0), (PX + 26.0, 9.5, zf), m["dark_steel"], g)
        for k in range(5):
            fz = z - 5.0 + 2.2 * k
            if fz < zf:
                box(f"p_fin_{i}_{k}", (PX + 2.0, 9.5, fz), (PX + 24.0, 12.0, min(fz + 0.8, zf)), m["steel"], g)
        box(f"p_tab_{i}", (PX + 26.0, 3.0, z - 2.0), (PX + 34.0, 5.0, z + 2.0), m["aqua"], g)
        if front:  # inside: a PCB, the DSP, a laser and a photodiode can
            box("p_pcb", (PX - 28.0, 2.0, z - 5.0), (PX + 22.0, 2.8, z + 0.02), m["board"], g)
            box("p_dsp", (PX - 18.0, 2.8, z - 4.0), (PX - 8.0, 4.4, z + 0.02), m["die"], g)
            for k, x in enumerate((PX + 8.0, PX + 15.0)):
                tube(f"p_can_{k}", (x, 4.8, z - 1.0), (x + 5.0, 4.8, z - 1.0), 1.8, m["steel"], g, 16)
    stream = empty("p_data", g)
    for i, dz in enumerate(mz):
        stream_of(stream, f"p_d{i}", 4, (30.0, 0.5, ZP + dz - 1.2), [(0, 0, 0), (PX - 62.0, 0, 0)], 0.9,
                  m["elec"], data_beat, 0.05, 0.8, 40)
    return g


def els(m, parent, x0, zc, mate_x, open_beat=None, pm=True):
    """The external laser source: a pluggable laser module through the front panel (inner end at x0,
    centred at zc), its two lasers inside, and two PM fibres glowing with CW light from its port
    round to FRONT's cable connector at mate_x. Returns (module group, cover group)."""
    g = empty("els", parent)
    box("els_base", (x0, 0.0, zc - 7.0), (x0 + 34.0, 2.0, zc + 7.0), m["dark_steel"], g)
    for s in (-1, 1):  # two laser chips, emitting toward the port
        box(f"els_laser_{s}", (x0 + 4.0, 2.0, zc + 3.0 * s - 1.2), (x0 + 8.0, 3.6, zc + 3.0 * s + 1.2), m["die"], g)
        box(f"els_facet_{s}", (x0 + 3.6, 2.4, zc + 3.0 * s - 0.6), (x0 + 4.0, 3.2, zc + 3.0 * s + 0.6), m["cw"], g)
        tube(f"els_out_{s}", (x0 - 1.5, 2.8, zc + 3.0 * s), (x0 + 3.6, 2.8, zc + 3.0 * s), 0.18, m["cw"], g, 8)
    cover = empty("els_cover", g)
    box("els_body", (x0, 2.0, zc - 7.0), (x0 + 34.0, 10.0, zc + 7.0), m["dark_steel"], cover)
    for k in range(6):
        z = zc - 6.0 + 2.4 * k
        box(f"els_fin{k}", (x0 + 14.0, 10.0, z), (x0 + 34.0, 13.0, z + 0.8), m["steel"], cover)
    box("els_pull", (x0 + 34.0, 3.0, zc - 2.0), (x0 + 40.0, 6.0, zc + 2.0), m["aqua"], g)
    box("els_port", (x0 - 1.5, 1.0, zc - 4.5), (x0, 5.0, zc + 4.5), m["plastic"], g)
    y = D.FIB_Y + 1.2
    for s, zl in zip((-1, 1), LZ if pm else ()):
        pts = [(x0 - 1.5, y, zc + 3.0 * s), (mate_x - 2.5, y, zc + 3.0 * s), (mate_x - 2.5, y, zl - 4.0), (mate_x, y, zl)]
        for i in range(3):
            tube(f"pm_{zl}_{i}", pts[i], pts[i + 1], 0.32, m["cladding"], parent, 10)
            tube(f"pmc_{zl}_{i}", pts[i], pts[i + 1], 0.18, m["cw"], parent, 8)
        tube(f"pm_drop_{zl}", (mate_x, y, zl), (mate_x, D.FIB_Y, zl), 0.32, m["cladding"], parent, 10)
    if open_beat is not None:  # lift the cover off for that beat (moved, not switched: see pd_glow)
        fly(cover, [(0, 0, 0), (0, 0, 0)], 0, F(open_beat, 0.15), steps=1)
        fly(cover, [(0, 30.0, 0), (0, 30.0, 0)], F(open_beat, 0.15) + 1, F(open_beat + 1, 0) - 1, steps=1)
    return g, cover


def link(m, root, els_open=None):
    """One switch board: the package, FRONT's cable to a panel adapter, the panel at x = 76 and the
    external laser beside the adapter. Returns (package dict, FRONT engine, ELS group)."""
    D.board(m, root, x1=82.0)
    pk = D.package(m, root)
    oe = pk["oes"][FRONT]
    D.mate(m, oe, 52.0)
    panel(m, root, 76.0, gaps=[(2.0, 15.0), (-27.0, -11.0)])
    g, _ = els(m, root, 66.0, -19.0, 62.5, open_beat=els_open)
    D.lit_lanes(m, oe, D.LASER, 7.0, D.FERRULE_U + 3.0)
    return pk, oe, g


def rows(m, root, data_beat=0, light_beat=1):
    """Sections 1 and 4: a pluggable switch (back row) and a CPO switch (front row) on one board,
    with the CPO row's external laser at the panel."""
    box("board_rows", (-70.0, -3.0, -135.0), (PX, 0.0, 125.0), m["board"], root)
    panel(m, root, PX, -135.0, 125.0, 14.0, gaps=[(ZP - 27.0, ZP + 27.0), (ZC - 27.0, ZC - 11.0)])
    pluggable_row(m, root, data_beat)
    cpo = empty("cpo_row", root)
    cpo.location = (0.0, -ZC, 0.0)  # Blender y is -z
    pk = D.package(m, cpo)
    for lat in D.OE_LAT:
        D.mate(m, pk["oes"][("+x", lat)], PX - 24.0)
    for lat in D.OE_LAT:
        d = pk["oes"][("+x", lat)]
        for v in D.TX:
            stream_of(d["g"], f"c_{lat}_{v}", 5, (7.5, D.FIB_Y, v), [(0, 0, 0), (21.0, 0, 0)], 0.45,
                      m["light"], light_beat, 0.0, 0.8, 24)
        # on the cable, the pulses ride its top face (the cable jacket is opaque)
        stream_of(d["g"], f"cc_{lat}", 6, (D.FERRULE_U + 11.0, D.FIB_Y + 0.6, 0.0),
                  [(0, 0, 0), (PX - 24.0 - D.FERRULE_U - 11.0, 0, 0)], 0.6, m["light"], light_beat, 0.0, 0.85, 60)
    els(m, cpo, PX - 10.0, -19.0, 62.5)
    D.lit_lanes(m, pk["oes"][FRONT], D.LASER, 7.0, D.FERRULE_U + 3.0)
    return pk


def pd_glow(m, d, beat):
    """The receive photodetectors of engine d lit for one beat. Parked under the board otherwise, not
    switched off: a thin box under an OFF-scaled group drops out of the export."""
    on = empty(f"pd_on_{d['side']}", d["g"])
    for i, v in enumerate(D.RX):
        box(f"pd_glow_{d['side']}_{v}", (1.0 + 0.9 * i, D.PIC_Y1, v - 0.3), (1.8 + 0.9 * i, D.PIC_Y1 + 0.14, v + 0.3),
            m["ring_on"], on)
    fly(on, [(0, -30.0, 0), (0, -30.0, 0)], 0, F(beat, 0.2), steps=1)
    fly(on, [(0, 0, 0), (0, 0, 0)], F(beat, 0.2) + 1, F(beat + 1, 0) - 1, steps=1)
    fly(on, [(0, -30.0, 0), (0, -30.0, 0)], F(beat + 1, 0), F(beat + 1, 0) + 1, steps=1)
    return on


def rings_on(m, d, beat):
    """The transmit rings flashing as the EIC drives them, and the laser bus glowing, from `beat` on."""
    wg = empty("wg_lit", d["g"])
    show(wg, upto(beat, 2))
    for v in D.LASER:
        box(f"wgl_{v}", (-1.2, D.PIC_Y1, v - 0.09), (7.0, D.PIC_Y1 + 0.05, v + 0.09), m["cw"], wg)
    box("bus_l", (-1.25, D.PIC_Y1, -3.6), (-0.95, D.PIC_Y1 + 0.05, 3.6), m["cw"], wg)
    on = empty("rings_on", d["g"])
    show(on, upto(beat, beat))
    for i, v in enumerate(D.TX):
        r = D.ring(f"ron_{v}", (1.2 + 1.1 * i, D.PIC_Y1 + 0.04, v + 0.45), 0.36, m["ring_on"], on, 0.1)
        flicker(r, F(beat, 0), F(beat + 1, 0), amps=(1.0, 0.2, 1.0, 1.0, 0.2, 1.0), every=5 + i)
    for v in D.TX:
        stream_of(d["g"], f"mod_{v}_{beat}", 4, (-0.9, D.PIC_Y1 + 0.1, v), [(0, 0, 0), (8.0, 0, 0)], 0.2,
                  m["light"], beat, 0.15, 0.85, 26)


def halo(m, parent, lo, hi, intervals, mt="hl"):
    g = group(parent, f"halo_{lo[0]:.0f}_{lo[2]:.0f}", intervals)
    box(f"halo_box_{lo[0]:.0f}_{lo[2]:.0f}", lo, hi, m[mt], g)
    return g


def finish_n(n):
    finish(f"section_{n}", page=PAGE)


# ---- 1. what happens: the optics move onto the switch package -----------------------------------


def sec1():
    m, root = begin(1)
    rows(m, root)
    W1 = lambda u, y, v: W(u, y, v, dz=ZC)  # noqa: E731
    tags(root, {
        0: [("SWITCH CHIP", (0.0, 6.0, ZP)),
            ("TENS OF CM OF BOARD TRACE", (80.0, 0.06, ZP + 22.2)),
            ("PLUGGABLE + DSP AT THE PANEL", (PX - 13.0, 4.4, ZP + 21.0))],
        1: [("OPTICAL ENGINES ON THE PACKAGE", W1(-4.0, 4.4, 0.0)),
            ("MILLIMETRES FROM THE CHIP", (0.0, 4.05, ZC + 2.0)),
            ("LIGHT LEAVES IN FIBRE", W1(70.0, D.FIB_Y + 0.45, 0.0))],
        2: [("EXTERNAL LASER AT THE PANEL", (PX + 10.0, 13.0, ZC - 19.0)),
            ("STEADY LIGHT IN BY FIBRE", (110.0, D.FIB_Y + 1.2, ZC - 22.0))],
    })
    cam(root, [
        pose((88.0, 4.0, ZP + 4.0), 165.0, 0.20, 1.00),
        pose((55.0, 4.0, ZC), 150.0, 0.30, 0.80),
        pose((148.0, 6.0, ZC - 16.0), 75.0, 0.55, 0.70),
    ])
    finish_n(1)


# ---- 2. the parts ---------------------------------------------------------------------------------


def sec2():
    m, root = begin(2)
    link(m, root)
    tags(root, {
        0: [("CO-PACKAGED OPTICS", (-24.0, 2.8, 39.0)),
            ("SWITCH CHIP", (-4.0, 4.05, 2.0)),
            ("OPTICAL ENGINE", W(-4.0, 4.4, 0.0))],
        1: [("MICRO-RING MODULATOR", W(2.3, D.PIC_Y1 + 0.05, -1.05)),
            ("PHOTODIODE", W(2.3, D.PIC_Y1 + 0.08, 1.5)),
            ("ELECTRONIC CHIP ON TOP", W(-4.0, 4.4, -1.5)),
            ("PHOTONIC CHIP", W(5.5, D.PIC_Y1, -3.9))],
        2: [("EXTERNAL LASER", (88.0, 13.0, -19.0)),
            ("FRONT PANEL", (77.0, 14.0, -2.0)),
            ("FIBRE PORT", (77.0, 7.0, 8.5))],
    })
    cam(root, [
        pose((4.0, 3.0, 4.0), 110.0, 0.40, 0.75),
        pose(W(2.0, 3.7, 0.0), 15.0, 0.30, 0.85),
        pose((76.0, 5.0, -5.0), 52.0, 0.55, 0.55),
    ])
    finish_n(2)


# ---- 3. a bit's path with CPO -------------------------------------------------------------------


def sec3():
    m, root = begin(3)
    pk, oe, _ = link(m, root)
    for i, v in enumerate(D.TX):  # 1: SerDes to the EIC over a few mm of package wiring
        u0 = 0.05 * i
        stream_of(oe["g"], f"data_{v}", 6, (-12.6, D.SUB_Y1 + 0.2, v), [(0, 0, 0), (6.8, 0, 0)], 0.3,
                  m["elec"], 0, u0, u0 + 0.8, 44)
    rings_on(m, oe, 1)  # 2-3: the EIC drives the rings, which imprint data on the laser light
    for v in D.TX:  # 4: out in fibre to the panel
        stream_of(oe["g"], f"out_{v}", 5, (7.5, D.FIB_Y, v), [(0, 0, 0), (44.0, 0, 0)], 0.42,
                  m["light"], 2, 0.0, 0.8, 50)
    for i, v in enumerate(D.RX):  # 5: receive, in from the panel to the photodiodes
        stream_of(oe["g"], f"in_{v}", 5, (51.5, D.FIB_Y, v), [(0, 0, 0), (-44.0, 0, 0), (-50.1 + 0.9 * i, D.PIC_Y1 - D.FIB_Y + 0.15, 0)],
                  0.42, m["light"], 2, 0.0, 0.8, 54)
    pd_glow(m, oe, 2)
    tags(root, {
        0: [("1 SERDES EDGE", (12.0, 4.05, 4.0)),
            ("A FEW MM OF PACKAGE WIRING", W(-9.5, 2.95, -1.5)),
            ("ELECTRONIC CHIP", W(-4.0, 4.4, 1.0))],
        1: [("2 EIC DRIVES THE RING", W(-4.0, 4.4, -2.0)),
            ("3 RING IMPRINTS THE DATA", W(2.3, D.PIC_Y1 + 0.05, -1.05)),
            ("LASER LIGHT IN", W(4.0, D.PIC_Y1 + 0.05, -3.5))],
        2: [("4 OUT IN FIBRE TO THE PANEL", W(22.0, D.FIB_Y, -1.5)),
            ("5 IN: GE PHOTODIODES + TIAS", W(2.3, D.PIC_Y1 + 0.1, 1.5))],
    })
    cam(root, [
        pose(W(-7.0, 3.2, 0.0), 20.0, 0.10, 1.05),
        pose(W(2.5, 3.7, 0.0), 12.0, 0.20, 1.00),
        pose(W(20.0, 3.6, 0.0), 48.0, 0.40, 0.70),
    ])
    finish_n(3)


# ---- 4. why: the copper is the problem ----------------------------------------------------------


def sec4():
    m, root = begin(4)
    pk = rows(m, root, data_beat=0, light_beat=2)
    d = pk["oes"][FRONT]
    for i, v in enumerate(D.LANES):  # the CPO hop: a few mm, data on every lane
        a, b = (-12.6, -5.8) if v < 0 else (-5.8, -12.6)
        u0 = 0.03 * ((i * 3) % 5)
        stream_of(d["g"], f"hop_{v}", 6, (a, D.SUB_Y1 + 0.2, v), [(0, 0, 0), (b - a, 0, 0)], 0.3,
                  m["elec"], 1, u0, u0 + 0.8, 44)
    W1 = lambda u, y, v: W(u, y, v, dz=ZC)  # noqa: E731
    tags(root, {
        0: [("200G PER LANE, LONG TRACE", (80.0, 0.06, ZP + 22.2)),
            ("A DSP IN EVERY MODULE", (PX - 13.0, 4.4, ZP + 21.0)),
            ("SWITCH CHIP", (0.0, 6.0, ZP))],
        1: [("MILLIMETRES OF WIRING", W1(-9.0, 2.84, -2.5)),
            ("ENGINE DRIVES THE OPTICS", W1(-4.0, 4.4, 0.0)),
            ("NO DSP", W1(3.0, D.PIC_Y1, -3.9))],
        2: [("PLUGGABLE: ~25 W PER 1.6T PORT", (0.0, 6.0, ZP)),
            ("CPO: ~9 W PER 1.6T PORT", (-4.0, 4.05, ZC + 2.0))],
    })
    cam(root, [
        pose((88.0, 4.0, ZP + 4.0), 165.0, 0.20, 1.00),
        pose(W1(-7.0, 3.2, 0.0), 22.0, 0.10, 1.05),
        pose((65.0, 4.0, -15.0), 290.0, 0.25, 0.85),
    ])
    finish_n(4)


# ---- 5. inside the optical engine ---------------------------------------------------------------


def sec5():
    m, root = begin(5)
    # Beat 0: the engine cut open down its middle lane, to show the electronic chip stacked on the
    # photonic one.
    D.CLIP = 8.5
    cutg = group(root, "cut", upto(0, 0))
    D.board(m, cutg)
    D.package(m, cutg)
    z = D.CLIP
    for i in range(24):
        x = 17.3 + 0.58 * i
        tube(f"pb_{i}", (x, D.SUB_Y1, z), (x, D.PIC_Y0, z), 0.1, m["solder"], cutg, 6)
    for i in range(12):
        x = 17.8 + 0.4 * i
        tube(f"eb_{i}", (x, D.PIC_Y1, z), (x, D.EIC_Y0, z), 0.07, m["solder"], cutg, 6)
    D.CLIP = None
    whole = group(root, "intact", upto(1, 2))
    D.board(m, whole)
    pk = D.package(m, whole)
    oe = pk["oes"][FRONT]
    D.lit_lanes(m, oe, D.LASER, 7.0, D.FERRULE_U)
    rings_on(m, oe, 1)
    # Beat 2: the rings warm up; each sits in a heater loop (copper arcs) that holds its resonance.
    for i, v in enumerate(D.TX):
        D.ring(f"heater_{v}", (1.2 + 1.1 * i, D.PIC_Y1 + 0.02, v + 0.45), 0.52, m["copper"], oe["g"], 0.05)
    warm = empty("ring_warm", oe["g"])
    show(warm, upto(2, 2))
    at = (2.3, 3.9, -1.0)
    pv = pivot("warm_pulse", at, warm)
    box("warm_box", rel(at, (0.4, D.PIC_Y1, -3.0)), rel(at, (4.3, 4.3, 0.2)), m["heat"], pv)
    flicker(pv, F(2, 0), F(3, 0), every=8)
    tags(root, {
        0: [("ELECTRONIC CHIP", (20.0, 4.15, z)),
            ("STACKED ON THE PHOTONIC CHIP", (19.0, 3.78, z)),
            ("PHOTONIC CHIP", (27.0, 3.35, z))],
        1: [("200G MICRO-RING MODULATORS", W(2.3, D.PIC_Y1 + 0.05, -1.05)),
            ("LASER LIGHT IN", W(4.0, D.PIC_Y1 + 0.05, -3.5)),
            ("VOLTAGE FROM THE EIC", W(-4.0, 4.4, -2.0))],
        2: [("RINGS DRIFT WITH TEMPERATURE", W(2.3, 4.3, -1.0)),
            ("HEATER LOOP KEEPS IT TUNED", W(3.4, D.PIC_Y1 + 0.02, -1.55))],
    })
    cam(root, [
        pose((22.5, 5.2, 8.5), 11.0, 0.12, 0.22),
        pose(W(2.5, 3.7, 0.0), 12.0, 0.20, 1.00),
        pose(W(2.4, 3.8, -1.0), 8.0, 0.35, 0.85),
    ])
    finish_n(5)


# ---- 6. lasers stay pluggable -------------------------------------------------------------------


def sec6():
    m, root = begin(6)
    pk, oe, g = link(m, root, els_open=2)
    # Beat 1: the module slides out of the panel and back, like any pluggable.
    fly(g, [(0, 0, 0), (0, 0, 0)], 0, F(1, 0.1), steps=1)
    fly(g, [(0, 0, 0), (26.0, 0, 0), (26.0, 0, 0), (0, 0, 0)], F(1, 0.1) + 1, F(1, 0.9), steps=6)
    tags(root, {
        0: [("EXTERNAL LASER MODULE", (88.0, 13.0, -19.0)),
            ("OUT AT THE COOL PANEL", (77.0, 14.0, -24.0)),
            ("LIGHT TO THE ENGINE BY FIBRE", (60.0, D.FIB_Y + 1.2, -6.0))],
        1: [("SWAPPED LIKE A PLUGGABLE", (104.0, 6.0, -19.0)),
            ("ENGINE STAYS IN PLACE", W(-4.0, 4.4, 0.0))],
        2: [("2 LASERS PER 1.6T LINK, NOT 8", (71.5, 3.6, -16.0)),
            ("CW LIGHT OUT", (64.0, 2.8, -16.0))],
    })
    cam(root, [
        pose((70.0, 5.0, -10.0), 55.0, 0.40, 0.65),
        pose((62.0, 5.0, -8.0), 95.0, 0.35, 0.75),
        pose((72.0, 4.0, -19.0), 26.0, 0.30, 0.90),
    ])
    finish_n(6)


# ---- 7. the switches ----------------------------------------------------------------------------


def sec7():
    m, root = begin(7)
    D.board(m, root, x1=82.0)
    pk = D.package(m, root)
    for lat in D.OE_LAT:
        D.mate(m, pk["oes"][("+x", lat)], 52.0)
    box("panel_face", (76.0, -3.0, -60.0), (78.0, 14.0, 60.0), m["steel"], root)
    ports = empty("ports", root)  # a front panel full of fibre ports
    for i in range(14):
        zc = -52.0 + 8.0 * i
        for r, y in enumerate((2.0, 8.0)):
            box(f"port_{i}_{r}", (78.0, y, zc - 3.0), (81.0, y + 4.0, zc + 3.0), m["dark_steel"], ports)
            box(f"port_in_{i}_{r}", (81.0, y + 1.2, zc - 1.8), (81.2, y + 2.8, zc + 1.8), m["aqua"], ports)
    for lat in D.OE_LAT:
        d = pk["oes"][("+x", lat)]
        for v in D.TX:
            stream_of(d["g"], f"sw_{lat}_{v}", 4, (7.5, D.FIB_Y, v), [(0, 0, 0), (44.0, 0, 0)], 0.42,
                      m["light"], 1, 0.0, 0.8, 50)
    cp = group(root, "cold_plate", upto(2, 2))  # liquid cooled, quadrant cut away
    box("plate_back", (-34.0, 4.5, -34.0), (34.0, 7.0, 0.0), m["plate"], cp)
    box("plate_front", (-34.0, 4.5, 0.0), (0.0, 7.0, 34.0), m["plate"], cp)
    tags(root, {
        0: [("SPECTRUM-X / QUANTUM-X PHOTONICS", (-4.0, 4.05, 2.0)),
            ("FROM 2H 2026 (SCHEDULED)", (-24.0, 2.8, 39.0)),
            ("8 ENGINES ON THE PACKAGE", W(-4.0, 4.4, 0.0))],
        1: [("128 x 800G OR 512 x 200G", (81.0, 10.0, 20.0)),
            ("FIBRE PORTS ON THE PANEL", (81.0, 4.0, -28.0))],
        2: [("~100 TB/S IN TOTAL", (-20.0, 7.0, 0.0)),
            ("BROADCOM: CPO TOMAHAWK TOO", (-24.0, 2.8, 39.0))],
    })
    cam(root, [
        pose((10.0, 3.0, 4.0), 115.0, 0.40, 0.75),
        pose((70.0, 6.0, 0.0), 80.0, 0.70, 0.45),
        pose((20.0, 4.0, 0.0), 140.0, 0.45, 0.70),
    ])
    finish_n(7)


# ---- 8. who makes it ----------------------------------------------------------------------------


def sec8():
    m, root = begin(8)
    pk, oe, g = link(m, root)
    tube("ext_cable", (79.0, D.FIB_Y + 3.0, 8.5), (170.0, D.FIB_Y + 3.0, 8.5), 1.6, m["aqua"], root, 16)
    halo(m, root, (-14.0, 2.8, -14.0), (14.0, 5.0, 14.0), upto(0, 0))
    for (s, lat), d in pk["oes"].items():
        h = group(d["g"], f"oe_halo_{s}_{lat}", upto(0, 0))
        box(f"oe_halo_box_{s}_{lat}", (-7.3, 2.9, -4.8), (12.3, 4.7, 4.8), m["hl"], h)
    halo(m, root, (65.0, -0.3, -27.0), (107.0, 14.0, -11.0), upto(1, 1))
    halo(m, root, (52.0, -0.3, 3.0), (130.0, 8.5, 14.0), upto(2, 2))
    tags(root, {
        0: [("NVIDIA, BROADCOM: SWITCH", (-4.0, 4.05, 2.0)),
            ("TSMC: CHIPS AND PACKAGING", W(-4.0, 4.4, 0.0))],
        1: [("LUMENTUM, COHERENT: LASERS", (88.0, 13.0, -19.0))],
        2: [("CORNING AND OTHERS: FIBRE", (100.0, D.FIB_Y + 4.6, 8.5)),
            ("CONNECTORS", W(31.0, 5.2, 0.0))],
    })
    cam(root, [
        pose((4.0, 3.0, 4.0), 105.0, 0.40, 0.75),
        pose((84.0, 5.0, -19.0), 50.0, 0.45, 0.65),
        pose((82.0, 4.0, 8.5), 75.0, 0.40, 0.60),
    ])
    finish_n(8)


# ---- 9. chokepoints and risks -------------------------------------------------------------------


def sec9():
    m, root = begin(9)
    pk, oe, g = link(m, root)
    bad = group(oe["g"], "bad_engine", upto(0, 0))
    box("bad_box", (-7.3, 2.9, -4.8), (7.3, 4.7, 4.8), m["bad"], bad)
    halo(m, root, (-75.5, -3.3, -75.5), (82.5, 5.5, 75.5), upto(0, 0))
    fau = group(oe["g"], "fau_halo", upto(1, 1))
    box("fau_halo_box", (6.8, 2.8, -4.8), (16.0, 4.4, 4.8), m["hl"], fau)
    halo(m, root, (-40.5, -0.3, -40.5), (40.5, 5.0, 40.5), upto(2, 2))
    tags(root, {
        0: [("FAILED ENGINE", W(0.0, 4.7, 0.0)),
            ("MEANS A NEW SWITCH BOARD", (-24.0, 2.8, 39.0))],
        1: [("FIBRE ATTACH: A NEW STEP", W(10.0, 4.05, 0.0)),
            ("LOW LOSS, AT SCALE", W(14.0, D.FIB_Y + 0.35, 2.0))],
        2: [("OPTICS TIED TO ONE VENDOR", (-4.0, 4.05, 2.0)),
            ("NOT AN OPEN MODULE MARKET", (77.0, 14.0, -2.0))],
    })
    cam(root, [
        pose((10.0, 3.0, 6.0), 95.0, 0.40, 0.75),
        pose(W(11.0, 3.5, 0.0), 16.0, 0.90, 0.50),
        pose((14.0, 3.0, 0.0), 125.0, 0.40, 0.70),
    ])
    finish_n(9)


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}

if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("--") + 1])
    if n not in SECTIONS:
        raise SystemExit(f"section must be 1..9, got {n}")
    SECTIONS[n]()
