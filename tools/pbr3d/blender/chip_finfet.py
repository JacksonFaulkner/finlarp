"""CHIP pictures for the FINFET node: the overview, zoom-ins a-e and sections 1-10.

Run from the repo root (through heavy.sh, one job at a time):

    blender -b --factory-startup --python tools/pbr3d/blender/chip_finfet.py -- [name ...]

With no names it builds everything. Names: overview, zoom_a .. zoom_e, sec1 .. sec10. Each scene
writes blender/chip_finfet_<name>.blend and assets/chip_finfet_<name>.glb (the overview is
assets/chip_finfet.glb). One beat is 8 s.

Overview beats:
  0 whole     the whole chip, the NMOS picked out: it is a FinFET
  1 planar    zoomed in: a planar gate sits on a flat channel, one face gated (a ghost)
  2 rise      the ghost goes; the channel stands up as a fin, raised source and drain at its ends
  3 wrap      the gate wraps the fin: a cap on top, a wall behind and a glass wall in front
  4 on        gate high: the channel fills the fin, the gate cap glows, current runs source to drain
  5 whole     gate low: the three faces pinch the channel shut; back out to the whole chip

Zoom and section scenes are three beats each. They use the same silicon and the same fin
(fin_parts), with the camera on the part they explain. The geometry is schematic, not to scale:
the fin runs along x (source to drain) and sits in depth (z) for width in fins. A side view puts
the camera on +x, cutting across the fins; a top view looks down on the gate row.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_zooms import finish, scale_keys, start  # noqa: E402
from sand_overview import OFF, beat, box, disc, empty, mat, show  # noqa: E402
import chip_kit as C  # noqa: E402
from chip_kit import F, glide_camera, label, overlay, route, stream_of  # noqa: E402

BEATS = 6  # the overview
ZBEATS = 3  # each zoom-in
SBEATS = 3  # each section

CX = C.NMOS_X  # the FinFET sits where the planar NMOS sits in the hero
SD = C.SD
GX0, GX1 = CX - C.GATE_HALF, CX + C.GATE_HALF  # the gate's length, along x
FZ = -60.0  # the fin's centre in depth: the contact plugs run at z = -60
FW = 56.0  # the fin's width in depth
FH = 150.0  # the fin's height above the silicon
TOX = 6.0  # high-k oxide between the fin and the gate metal
GT = 12.0  # gate metal thickness
EPI = 170.0  # the raised source and drain sit a little above the fin top
FP = 96.0  # fin pitch across the depth (z), so the fins sit side by side in width
PS = 2.5  # scene units per nm of gate pitch (schematic)

ZB = FZ - FW / 2 - TOX - GT  # the back gate wall's outer face
ZF = FZ + FW / 2 + TOX + GT  # the front gate wall's outer face

ZOOM1 = ((CX, 90.0, 0.0), 1400.0, 0.0, 0.10)
ZOOM2 = ((CX + 20.0, 120.0, 0.0), 1250.0, 0.35, 0.40)
POSES = [C.WHOLE, ZOOM1, ZOOM1, ZOOM2, ZOOM2, C.WHOLE]

# the camera poses of the zoom-ins and sections: (target, distance, yaw, pitch)
SIDE_YAW = math.pi / 2  # camera on +x: a cross-section across the fins
THREE_Q = (0.35, 0.40)  # yaw, pitch of the three-quarter view


def side(dist, target=(CX, 90.0, FZ), pitch=0.12):
    return (target, dist, SIDE_YAW, pitch)


def three_q(dist, target=(CX, 110.0, FZ)):
    return (target, dist, THREE_Q[0], THREE_Q[1])


def top(dist, target=(CX, 60.0, FZ)):
    return (target, dist, 0.0, 1.2)


def front(dist, target=(0.0, 200.0, 0.0)):
    return (target, dist, 0.0, 0.05)


def mats_finfet(m):
    m["f_fin"] = mat("chip_finfet_fin", (0.45, 0.62, 0.80), rough=0.3)
    m["f_glass"] = mat("chip_finfet_glass", (0.60, 0.66, 0.78), metal=0.6, rough=0.2, alpha=0.3)
    m["f_ghost"] = mat("chip_finfet_ghost", (0.75, 0.80, 0.90), rough=0.3, alpha=0.22)
    m["f_hl"] = mat("chip_finfet_hl", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=1.0, alpha=0.16)
    m["f_mask"] = mat("chip_finfet_mask", (0.86, 0.86, 0.92), metal=0.3, rough=0.35)
    m["f_wafer"] = mat("chip_finfet_wafer", (0.70, 0.76, 0.84), metal=0.5, rough=0.25)
    m["f_tool"] = mat("chip_finfet_tool", (0.30, 0.34, 0.42), metal=0.6, rough=0.5)


def fin_parts(g, m, cx=CX, zc=FZ, xs=None, epi=True, chan_on=None, gate_on=None):
    """The FinFET NMOS: the fin, its raised source and drain, the high-k oxide and the gate that
    wraps the fin's top and both sides. The front gate wall is drawn as glass so the fin reads
    through it. `xs` shortens the fin along x (a cut through the gate has no source and drain);
    `chan_on` and `gate_on` are the intervals the channel and the gate cap glow. Built in poly
    coordinates under `g`. Returns the groups fin, hk and gate, so a scene can switch them."""
    x0, x1 = xs if xs else (cx - SD - 80, cx + SD + 80)
    gx0, gx1 = cx - C.GATE_HALF, cx + C.GATE_HALF
    zb = zc - FW / 2 - TOX - GT
    zf = zc + FW / 2 + TOX + GT
    fin = empty("fin_g", g)
    box("fin", (x0, -40, zc - FW / 2), (x1, FH, zc + FW / 2), m["f_fin"], fin)
    if epi:
        for k, x in enumerate((cx - SD, cx + SD)):
            box(f"epi{k}", (x - 75, -40, zc - 50), (x + 75, EPI, zc + 50), m["c_nplus"], fin)
    hk = empty("hk_g", g)
    box("hk_top", (gx0, FH, zc - FW / 2 - TOX), (gx1, FH + TOX, zc + FW / 2 + TOX), m["c_oxide"], hk)
    box("hk_back", (gx0, 0, zc - FW / 2 - TOX), (gx1, FH, zc - FW / 2), m["c_oxide"], hk)
    box("hk_front", (gx0, 0, zc + FW / 2), (gx1, FH, zc + FW / 2 + TOX), m["c_oxide"], hk)
    gate = empty("gate_g", g)
    box("gate_cap", (gx0, FH + TOX, zb), (gx1, FH + TOX + GT, zf), m["c_gate"], gate)
    box("gate_back", (gx0, 0, zb), (gx1, FH + TOX + GT, zb + GT), m["c_gate"], gate)
    box("gate_front", (gx0, 0, zc + FW / 2 + TOX), (gx1, FH + TOX + GT, zf), m["f_glass"], gate)
    if chan_on:
        # the channel: the fin under the gate, glowing when it is on
        overlay(g, "chan_on", (gx0, -2, zc - FW / 2 - 3), (gx1, FH + 3, zc + FW / 2 + 3), m["c_chan"], chan_on)
    if gate_on:
        # the gate cap lights up while the gate is high
        overlay(g, "gate_on", (gx0 - 4, FH + TOX - 1, zb - 4), (gx1 + 4, FH + TOX + GT + 4, zf + 4),
                m["c_gate_on"], gate_on)
    return {"fin": fin, "hk": hk, "gate": gate}


def rows(parent, m, n, cx=CX, **kw):
    """n fins side by side in depth, centred on FZ: the width of a device in whole fins."""
    g = empty(f"rows{n}", parent)
    for k in range(n):
        fin_parts(g, m, cx=cx, zc=FZ + (k - (n - 1) / 2) * FP, **kw)
    return g


def plural(n):
    return f"{n} fin" if n == 1 else f"{n} fins"


def base(name, beats):
    """A fresh scene with the silicon, the materials and the fin's materials."""
    m, root = start(name, beats, page="chip")
    C.mats(m)
    mats_finfet(m)
    C.silicon(root, m)
    return m, root


def save(name):
    finish(name, page="chip")


def build():
    """The overview: the whole chip, zoomed in on the NMOS, which is a FinFET."""
    m, root = start("finfet", BEATS, page="chip")
    C.mats(m)
    mats_finfet(m)

    # the chip, as in the hero, but without chip_kit's planar NMOS: silicon, the planar PMOS,
    # contacts, the three wiring tiers and the bumps
    C.silicon(root, m)
    C.transistor(root, m, C.PMOS_X, False)
    C.contacts(root, m)
    C.wiring(root, m)
    C.bumps(root, m)

    # the FinFET: a group that is hidden during the planar beat and rises out of the silicon in beat 2
    rise = empty("finfet_rise", root)
    fin_parts(rise, m, chan_on=[(F(4, 0.05), F(5, 0))], gate_on=[(F(4, 0), F(5, 0))])
    scale_keys(
        rise,
        [(0, (1, 1, 1)), (F(1, 0), (OFF, OFF, OFF)), (F(2, 0), (OFF, OFF, OFF)), (F(2, 0.5), (1, 1, 1))],
        until=F(1, 0),
    )

    # beat 1: the planar comparison, a ghost gate lying flat on a flat channel
    overlay(root, "planar_gate", (GX0, 14, -240), (GX1, 120, 0), m["f_ghost"], [(F(1, 0), F(2, 0.15))])
    overlay(root, "planar_chan", (CX - SD, -30, -230), (CX + SD, 4, -6), m["c_chan"],
            [(F(1, 0), F(2, 0.15))])

    # the NMOS picked out in the whole chip (beat 0), and again on the way back out
    overlay(root, "finfet_hl", (CX - 330, -140, -250), (CX + 330, 190, 14), m["f_hl"],
            [(F(0, 0), F(1, 0)), (F(5, 0.1), F(6, 0))])

    # electrons run along the fin from the source to the drain while the channel is on
    s, p = route([(CX - SD, 75.0, 0.0), (CX + SD, 75.0, 0.0)])
    stream_of(root, "elec", 9, s, p, 20, m["c_dot_sig"], 4, 0.05, 0.6, 100)

    label("FinFET", (CX, 230.0, 0), root, [(F(0, 0), F(1, 0))])
    label("planar gate: one face", (CX, 150.0, 0), root, [(F(1, 0), F(2, 0.15))])
    label("flat channel", (CX - 300.0, -20.0, 0), root, [(F(1, 0), F(2, 0.15))])
    label("fin: channel stood up", (CX - 300.0, 120.0, 0), root, [(F(2, 0.5), F(6, 0))])
    label("source", (CX - SD, 200.0, 0), root, [(F(2, 0.5), F(5, 0))])
    label("drain", (CX + SD, 200.0, 0), root, [(F(2, 0.5), F(5, 0))])
    label("gate: three sides", (CX, 260.0, 0), root, [(F(3, 0), F(4, 0))])
    label("gate high: channel on", (CX, 260.0, 0), root, [(F(4, 0.05), F(5, 0))])
    label("gate low: pinched, less leak", (CX, 260.0, 0), root, [(F(5, 0.05), F(6, 0))])

    C.glide_camera(root, POSES)


# ---- zoom-ins a-e ----------------------------------------------------------------------------


def zoom_a():
    """a, making fins: SAQP masks, the fin etched up, the oxide recessed (cross-section)."""
    name = "finfet_zoom_a"
    m, root = base(name, ZBEATS)
    masks = empty("masks", root)
    for k in range(8):
        z = FZ + (k - 3.5) * 48.0
        box(f"mask{k}", (CX - 300, 0, z - 9), (CX + 300, 70, z + 9), m["f_mask"], masks)
    show(masks, beat(0))
    fins = empty("fins", root)
    for k in range(4):
        zc = FZ + (k - 1.5) * FP
        box(f"fin{k}", (CX - 300, -40, zc - FW / 2), (CX + 300, FH, zc + FW / 2), m["f_fin"], fins)
    scale_keys(fins, [(0, (OFF, OFF, OFF)), (F(1, 0), (1, 1, OFF)), (F(1, 0.6), (1, 1, 1))], until=F(1, 0))
    ox = empty("oxide", root)
    z0, z1 = FZ - 1.5 * FP - FW / 2 - 14, FZ + 1.5 * FP + FW / 2 + 14
    box("sti", (CX - 320, 0, z0), (CX + 320, FH, z1), m["f_glass"], ox)
    scale_keys(ox, [(0, (OFF, OFF, OFF)), (F(2, 0), (1, 1, 1)), (F(2, 0.6), (1, 1, 0.47))], until=F(2, 0))
    label("SAQP: quarter-pitch masks", (CX, 170.0, FZ), root, beat(0))
    label("FIN FORM: etch the silicon", (CX, 170.0, FZ), root, [(F(1, 0.5), F(2, 0))])
    label("FIN REVEAL: oxide recessed", (CX, 170.0, FZ), root, [(F(2, 0.5), F(3, 0))])
    glide_camera(root, [side(1700.0, pitch=0.06), side(1400.0, pitch=0.06), side(1250.0, pitch=0.06)])
    save(name)


def zoom_b():
    """b, the gate wraps three sides: high-k, the gate metal, then the gate on (three-quarter)."""
    name = "finfet_zoom_b"
    m, root = base(name, ZBEATS)
    g = empty("finfet", root)
    p = fin_parts(g, m, chan_on=beat(2), gate_on=beat(2))
    show(p["hk"], [(F(0, 0), F(3, 0))])
    show(p["gate"], [(F(1, 0), F(3, 0))])
    s, pth = route([(CX - SD, 75.0, FZ), (CX + SD, 75.0, FZ)])
    stream_of(root, "elec", 9, s, pth, 20, m["c_dot_sig"], 2, 0.05, 0.6, 100)
    s, pth = route([(GX0 - 60, 8.0, FZ), (GX1 + 60, 8.0, FZ)])
    stream_of(root, "leak", 9, s, pth, 16, m["c_dot_out"], 2, 0.2, 0.8, 90)
    label("high-k: top and sidewalls", (CX, 230.0, FZ), root, beat(0))
    label("gate metal: three sides", (CX, 260.0, FZ), root, beat(1))
    label("on: current along the fin", (CX, 260.0, FZ), root, beat(2))
    label("sub-fin: not gated", (GX0 - 60, 40.0, FZ), root, beat(2))
    glide_camera(root, [three_q(900.0), three_q(800.0), three_q(800.0)])
    save(name)


def zoom_c():
    """c, fin count: one, two, three fins side by side (top view)."""
    name = "finfet_zoom_c"
    m, root = base(name, ZBEATS)
    texts = ("one fin: low drive", "two fins: 2x drive", "three fins: 3x drive")
    for n in (1, 2, 3):
        show(rows(root, m, n), beat(n - 1))
        label(texts[n - 1], (CX, 200.0, FZ), root, beat(n - 1))
    glide_camera(root, [top(1000.0), top(1000.0), top(1000.0)])
    save(name)


def finflex(name):
    """d, FinFlex: two cell blocks with 3-2, 2-2 then 2-1 fins (top view)."""
    m, root = base(name, ZBEATS)
    combos = [(3, 2), (2, 2), (2, 1)]  # left and right block fin counts, beat by beat
    for side_i, cx in enumerate((CX - 300.0, CX + 300.0)):
        for n in (1, 2, 3):
            on = [i for i, c in enumerate(combos) if c[side_i] == n]
            if on:
                g = rows(root, m, n, cx=cx, xs=(cx - 170, cx + 170), epi=False)
                show(g, [(F(i, 0), F(i + 1, 0)) for i in on])
    label("3-2 cells: speed", (CX, 240.0, FZ), root, beat(0))
    label("2-2 cells: balanced", (CX, 240.0, FZ), root, beat(1))
    label("2-1 cells: low power, dense", (CX, 240.0, FZ), root, beat(2))
    glide_camera(root, [top(1500.0), top(1500.0), top(1500.0)])
    save(name)


def limits(name):
    """e and section 7: the fin gets thinner and taller, sub-fin leakage, then nanosheets."""
    m, root = base(name, ZBEATS)
    tall = empty("tall", root)
    box("tall", (CX - 150, -40, FZ - FW * 0.3), (CX + 150, FH * 1.6, FZ + FW * 0.3), m["f_fin"], tall)
    show(tall, beat(0))
    norm = empty("normal", root)
    fin_parts(norm, m, chan_on=None)
    show(norm, beat(1))
    s, pth = route([(GX0 - 60, 8.0, FZ), (GX1 + 60, 8.0, FZ)])
    stream_of(root, "leak", 9, s, pth, 16, m["c_dot_out"], 1, 0.2, 0.8, 90)
    sheets = empty("sheets", root)
    for k, y0 in enumerate((40.0, 95.0, 150.0)):
        box(f"sheet{k}", (CX - 150, y0, FZ - FW / 2), (CX + 150, y0 + 14, FZ + FW / 2), m["f_fin"], sheets)
    box("wrap", (CX - 150, 30, FZ - FW / 2 - TOX - GT), (CX + 150, 180, FZ + FW / 2 + TOX + GT), m["f_glass"],
        sheets)
    show(sheets, beat(2))
    label("fin: thinner and taller", (CX, 260.0, FZ), root, beat(0))
    label("sub-fin leakage, GIDL", (CX, 260.0, FZ), root, beat(1))
    label("nanosheets: gate on four sides", (CX, 260.0, FZ), root, beat(2))
    glide_camera(root, [side(800.0, pitch=0.12), three_q(800.0), side(800.0, pitch=0.12)])
    save(name)


def zoom_e():
    limits("finfet_zoom_e")


# ---- sections 1-10 ---------------------------------------------------------------------------


def sec1():
    """1, what happens: the channel stands up as a fin, the gate wraps it, width in whole fins."""
    name = "finfet_sec1"
    m, root = base(name, SBEATS)
    main = empty("main", root)
    p = fin_parts(main, m)
    scale_keys(p["fin"], [(0, (OFF, OFF, OFF)), (F(0, 0.1), (1, 1, OFF)), (F(0, 0.7), (1, 1, 1))],
               until=F(0, 0.1))
    show(main, [(0, F(2, 0))])
    show(p["hk"], [(F(1, 0), F(2, 0))])
    show(p["gate"], [(F(1, 0), F(2, 0))])
    for n, iv in ((1, (F(2, 0), F(2, 1 / 3))), (2, (F(2, 1 / 3), F(2, 2 / 3))), (3, (F(2, 2 / 3), F(3, 0)))):
        show(rows(root, m, n), [iv])
    label("fins: the channel stands up", (CX, 240.0, FZ), root, beat(0))
    label("gate wrap: three sides", (CX, 240.0, FZ), root, beat(1))
    label("width: 1, 2 or 3 fins", (CX, 240.0, FZ), root, beat(2))
    glide_camera(root, [three_q(900.0), three_q(800.0), three_q(1100.0)])
    save(name)


def sec2():
    """2, the fin under the gate: Hfin and Wfin, the high-k and gate metal, the ungated bottom."""
    name = "finfet_sec2"
    m, root = base(name, SBEATS)
    g = empty("cut", root)
    p = fin_parts(g, m, xs=(GX0 - 10, GX1 + 10), epi=False)
    show(p["hk"], [(F(1, 0), F(3, 0))])
    show(p["gate"], [(F(1, 0), F(3, 0))])
    s, pth = route([(GX0 - 60, 8.0, FZ), (GX1 + 60, 8.0, FZ)])
    stream_of(root, "leak", 9, s, pth, 16, m["c_dot_out"], 2, 0.2, 0.8, 90)
    label("Hfin: tens of nm", (CX, FH, FZ), root, beat(0))
    label("Wfin: a few nm to 10 nm", (CX, 60.0, FZ + FW / 2 + 40), root, beat(0))
    label("high-k and gate metal", (CX, 240.0, FZ), root, beat(1))
    label("sub-fin: not gated", (GX0 - 60, 40.0, FZ), root, beat(2))
    glide_camera(root, [side(700.0, target=(CX, 80.0, FZ)), side(700.0, target=(CX, 80.0, FZ)),
                        three_q(800.0, target=(CX, 80.0, FZ))])
    save(name)


def gate_row(parent, m, pitch, zc):
    """A row of gate caps along one fin, `pitch` apart (top view). The gate is half the pitch."""
    g = empty("gate_row", parent)
    box("fin_row", (CX - 420, -40, zc - FW / 2), (CX + 420, FH, zc + FW / 2), m["f_fin"], g)
    gl = pitch * 0.5
    for k in range(4):
        x = CX + (k - 1.5) * pitch
        box(f"gcap{k}", (x - gl / 2, FH + TOX, zc - FW / 2 - TOX - GT), (x + gl / 2, FH + TOX + GT, zc + FW / 2 + TOX + GT),
            m["c_gate"], g)
    return g


def sec3():
    """3, node history: the gate pitch from 16 to N3, the fin stretched, not replaced."""
    name = "finfet_sec3"
    m, root = base(name, SBEATS)
    show(gate_row(root, m, 90.0 * PS, FZ), beat(0))
    show(gate_row(root, m, 57.0 * PS, FZ - 110.0), beat(1))
    show(gate_row(root, m, 51.0 * PS, FZ + 110.0), beat(1))
    show(gate_row(root, m, 45.0 * PS, FZ), beat(2))
    label("TSMC N16: gate pitch 90 nm", (CX - 200.0, 200.0, FZ), root, beat(0))
    label("N7: 57 nm (est), N5: 51 nm", (CX - 200.0, 200.0, FZ), root, beat(1))
    label("TSMC N3: gate pitch 45 nm", (CX - 200.0, 200.0, FZ), root, beat(2))
    glide_camera(root, [top(1100.0), top(1100.0), top(950.0)])
    save(name)


def sec4():
    """4, by the numbers: a fixed frame holding more transistor tiles at each node."""
    name = "finfet_sec4"
    m, root = base(name, SBEATS)
    w = 400.0
    frame = empty("frame", root)
    box("fr_a", (CX - w / 2 - 6, 0, FZ - w / 2 - 6), (CX + w / 2 + 6, 12, FZ - w / 2), m["f_mask"], frame)
    box("fr_b", (CX - w / 2 - 6, 0, FZ + w / 2), (CX + w / 2 + 6, 12, FZ + w / 2 + 6), m["f_mask"], frame)
    box("fr_c", (CX - w / 2 - 6, 0, FZ - w / 2), (CX - w / 2, 12, FZ + w / 2), m["f_mask"], frame)
    box("fr_d", (CX + w / 2, 0, FZ - w / 2), (CX + w / 2 + 6, 12, FZ + w / 2), m["f_mask"], frame)
    for i, (cols, nrows, node) in enumerate(((6, 6, "N7"), (7, 8, "N5"), (9, 10, "N3"))):
        g = empty(f"tiles_{node}", root)
        px, pz = w / cols, w / nrows
        for c in range(cols):
            for r in range(nrows):
                x = CX - w / 2 + (c + 0.5) * px
                z = FZ - w / 2 + (r + 0.5) * pz
                box(f"t{node}_{c}_{r}", (x - px * 0.3, 0, z - pz * 0.3), (x + px * 0.3, 30, z + pz * 0.3),
                    m["f_fin"], g)
        show(g, beat(i))
    label("N7: about 91 MTr/mm2 (est)", (CX, 200.0, FZ - w / 2), root, beat(0))
    label("N5: about 138 MTr/mm2", (CX, 200.0, FZ - w / 2), root, beat(1))
    label("N3: 1.6x N5", (CX, 200.0, FZ - w / 2), root, beat(2))
    glide_camera(root, [top(900.0, target=(CX, 40.0, FZ)), top(900.0, target=(CX, 40.0, FZ)),
                        top(900.0, target=(CX, 40.0, FZ))])
    save(name)


def sec5():
    finflex("finfet_sec5")


def sec6():
    """6, TSMC wafer revenue by node in 2025: the 7 nm and below, 5 nm and 3 nm bars."""
    name = "finfet_sec6"
    m, root = start(name, SBEATS, page="chip")
    C.mats(m)
    mats_finfet(m)
    bars = ((-220.0, 74, "7 nm and below: 74%"), (0.0, 36, "5 nm: about 35-37%"), (220.0, 28, "3 nm: 28% in Q4"))
    for i, (x, pct, text) in enumerate(bars):
        h = pct * 5.0
        box(f"bar{i}", (x - 75, 0, -60), (x + 75, h, 60), m["f_fin"], root)
        overlay(root, f"hi{i}", (x - 84, -4, -70), (x + 84, h + 6, 70), m["c_chan"], beat(i))
        label(text, (x, h + 40.0, 0.0), root, beat(i))
    box("ground", (-380, -10, -120), (380, 0, 120), m["f_mask"], root)
    glide_camera(root, [front(1100.0), front(1100.0), front(1100.0)])
    save(name)


def sec7():
    limits("finfet_sec7")


def sec8():
    """8, who makes it: TSMC's FinFET rows, Intel and Samsung, the litho and etch tools."""
    name = "finfet_sec8"
    m, root = base(name, SBEATS)
    show(rows(root, m, 3), beat(0))
    show(rows(root, m, 1), beat(1))
    show(rows(root, m, 2), beat(2))
    tools = empty("tools", root)
    box("tool_l", (CX - 470, 0, FZ - 160), (CX - 390, 240, FZ + 160), m["f_tool"], tools)
    box("tool_r", (CX + 390, 0, FZ - 160), (CX + 470, 240, FZ + 160), m["f_tool"], tools)
    show(tools, beat(2))
    label("TSMC: N16 to N3 rows", (CX, 260.0, FZ), root, beat(0))
    label("Intel and Samsung: FinFETs", (CX, 260.0, FZ), root, beat(1))
    label("litho and etch tools", (CX, 290.0, FZ), root, beat(2))
    glide_camera(root, [three_q(1600.0), three_q(1600.0), three_q(1600.0)])
    save(name)


def sec9():
    """9, chokepoints and risks: fins out of room, wafer cost, the estimates."""
    name = "finfet_sec9"
    m, root = base(name, SBEATS)
    tall = empty("tall", root)
    box("tall", (CX - 150, -40, FZ - FW * 0.3), (CX + 150, FH * 1.6, FZ + FW * 0.3), m["f_fin"], tall)
    show(tall, beat(0))
    stacks = empty("wafers", root)
    for i, (x, n) in enumerate(((CX - 400.0, 2), (CX, 3), (CX + 400.0, 4))):
        for k in range(n):
            disc(f"w{i}_{k}", (x, 6.0 + 14.0 * k, FZ), 130.0, 12.0, m["f_wafer"], stacks)
    show(stacks, [(F(1, 0), F(3, 0))])
    cut = empty("cut", root)
    fin_parts(cut, m, xs=(GX0 - 10, GX1 + 10), epi=False)
    show(cut, beat(2))
    label("fins: out of room below 3 nm", (CX, 260.0, FZ), root, beat(0))
    label("rising cost: no public price", (CX, 150.0, FZ), root, beat(1))
    label("pitches: WikiChip estimates", (CX, 240.0, FZ), root, beat(2))
    glide_camera(root, [side(800.0), three_q(1500.0, target=(CX, 60.0, FZ)), side(700.0)])
    save(name)


def sec10():
    """10, sources: the whole chip, slow pull-back."""
    name = "finfet_sec10"
    m, root = start(name, SBEATS, page="chip")
    C.mats(m)
    mats_finfet(m)
    C.silicon(root, m)
    C.transistor(root, m, C.PMOS_X, False)
    C.contacts(root, m)
    C.wiring(root, m)
    C.bumps(root, m)
    fin_parts(empty("finfet", root), m)
    glide_camera(root, [C.WHOLE, ((0.0, 620.0, 0.0), 6400.0, 0.04, 0.10), ((0.0, 620.0, 0.0), 7200.0, 0.10, 0.12)])
    save(name)


SCENES = {
    "zoom_a": zoom_a,
    "zoom_b": zoom_b,
    "zoom_c": zoom_c,
    "zoom_d": lambda: finflex("finfet_zoom_d"),
    "zoom_e": zoom_e,
    "sec1": sec1,
    "sec2": sec2,
    "sec3": sec3,
    "sec4": sec4,
    "sec5": sec5,
    "sec6": sec6,
    "sec7": sec7,
    "sec8": sec8,
    "sec9": sec9,
    "sec10": sec10,
}


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = args or ["overview"] + list(SCENES)
    for name in names:
        if name == "overview":
            build()
            finish("finfet", page="chip")
        else:
            SCENES[name]()
