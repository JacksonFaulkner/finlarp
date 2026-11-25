"""TRM_RACK_DENSITY: the Terms-tab overview for rack density (kW per rack).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_rack_density.py

Writes assets/term_TRM_RACK_DENSITY.glb and specs/terms/TRM_RACK_DENSITY.json.

Units are centimetres (a rack is 60 wide, 120 deep, ~200 tall). This file also holds the small
rack kit (materials, an NVL72-class AI rack cut open down its +x side, an air-cooled enterprise
rack, a CDU, kW meters, floor) that trm_gpu_cluster / trm_hot_aisle / trm_rack_integration import.

Beats:
  0 compare   a 10 kW enterprise rack beside a 130 kW AI rack, kW meters, power beads into each
  1 inside    the AI rack's side off: power shelves, 18 compute trays (72 GPUs), 9 NVLink switch trays
  2 heat      the old rack breathes air; the AI rack needs liquid: CDU, manifolds, cold plates
  3 power     overhead busway, tap box, rear 50 V busbar; ~1.4 t on the floor
  4 retrofit  one AI rack draws what a row of 13 old racks did: halls must be rebuilt
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, P, beat, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, mat  # noqa: E402

SLUG = "TRM_RACK_DENSITY"
BEATS = [
    ("An AI rack draws ten times what an old server rack did",
     "Rack density is the power one rack pulls, in kilowatts. A typical enterprise rack of 2U servers ran 5-15 kW, "
     "and data halls were built around that. An Nvidia GB200 NVL72 rack draws about 120-130 kW, and the next "
     "generations are planned at several hundred kW up to around 1 MW per rack."),
    ("Inside: 72 GPUs packed into one cabinet",
     "The NVL72 holds 18 compute trays with four Blackwell GPUs and two Grace CPUs each, nine NVLink switch trays "
     "between them, and power shelves top and bottom. Packing them this close lets all 72 GPUs talk over copper "
     "NVLink as one big GPU, which is the whole point, and it is also why the power ends up in one place."),
    ("Air cannot carry 130 kW out of a rack; liquid has to",
     "An old rack pulls cool air in the front and blows warm air out the back, and fans handle 10-20 kW fine. At "
     "130 kW the air would have to move impossibly fast, so cold plates sit on every GPU and CPU and a coolant "
     "distribution unit (CDU) pumps water-glycol through manifolds at the back of the rack. Water holds about "
     "3,500 times more heat than the same volume of air."),
    ("Power and weight both concentrate",
     "Power comes from an overhead busway through a tap box into power shelves that turn AC into ~50 V DC on a copper "
     "busbar down the back. A full rack weighs around 1.4 tonnes, more than many raised floors were rated for, "
     "so new halls put racks on slab and run power and pipes overhead."),
    ("One AI rack = a whole row of old racks: halls need retrofits",
     "A 130 kW rack draws what thirteen 10 kW racks did, in one floor tile, so older sites run out of power, cooling "
     "and floor strength long before space. That drives retrofits and new builds: Nvidia (NVDA) sets the rack spec, "
     "Super Micro (SMCI) builds racks, Vertiv (VRT) supplies power and cooling, and Equinix (EQIX) re-fits halls."),
]

# ---- rack kit ---------------------------------------------------------------------------------

U = 4.45  # one rack unit
RW, RD, RH = 30.0, 60.0, 205.0  # half width, half depth, height
Y0 = 6.0  # first slot
LAYOUT = ["shelf"] * 4 + ["compute"] * 10 + ["switch"] * 9 + ["compute"] * 8 + ["shelf"] * 4 + ["net"]

_batch = {}


def fb(name, lo, hi, mt, parent=None):
    """Queue a box for `flush` (one mesh per parent + material: far faster than one op per box)."""
    _batch.setdefault((parent.name if parent else "", mt.name), (parent, mt, []))[2].append((lo, hi))
    return None


def flush(name):
    import bpy
    for (pn, mn), (parent, mt, boxes) in list(_batch.items()):
        vs, fs = [], []
        for lo, hi in boxes:
            a, b = P(*lo), P(*hi)
            X = (min(a.x, b.x), max(a.x, b.x))
            Y = (min(a.y, b.y), max(a.y, b.y))
            Z = (min(a.z, b.z), max(a.z, b.z))
            n = len(vs)
            vs += [(X[i], Y[j], Z[k]) for i in (0, 1) for j in (0, 1) for k in (0, 1)]
            v = lambda i, j, k: n + i * 4 + j * 2 + k  # noqa: E731
            fs += [(v(0, 0, 0), v(0, 0, 1), v(0, 1, 1), v(0, 1, 0)), (v(1, 0, 0), v(1, 1, 0), v(1, 1, 1), v(1, 0, 1)),
                   (v(0, 0, 0), v(1, 0, 0), v(1, 0, 1), v(0, 0, 1)), (v(0, 1, 0), v(0, 1, 1), v(1, 1, 1), v(1, 1, 0)),
                   (v(0, 0, 0), v(0, 1, 0), v(1, 1, 0), v(1, 0, 0)), (v(0, 0, 1), v(1, 0, 1), v(1, 1, 1), v(0, 1, 1))]
        me = bpy.data.meshes.new(f"{name}_{mn}")
        me.from_pydata(vs, [], fs)
        me.update()
        me.materials.append(mt)
        o = bpy.data.objects.new(f"{name}_{mn}", me)
        bpy.context.collection.objects.link(o)
        o.parent = parent
    _batch.clear()


def slot_y(i):
    return Y0 + 2.0 + U * i


def mats(m):
    new = {
        "frame": ((0.10, 0.10, 0.12), 0.6, 0.45),
        "frame2": ((0.22, 0.23, 0.26), 0.7, 0.4),
        "bezel_c": ((0.16, 0.17, 0.19), 0.6, 0.4),
        "bezel_s": ((0.30, 0.32, 0.36), 0.8, 0.35),
        "bezel_p": ((0.50, 0.52, 0.55), 0.8, 0.35),
        "srv": ((0.62, 0.63, 0.65), 0.7, 0.4),
        "blank": ((0.06, 0.06, 0.07), 0.3, 0.6),
        "grill": ((0.03, 0.03, 0.035), 0.2, 0.7),
        "tray": ((0.55, 0.57, 0.60), 0.85, 0.35),
        "pcb_g": ((0.07, 0.30, 0.16), 0.0, 0.55),
        "coldp": ((0.82, 0.50, 0.30), 0.9, 0.3),
        "hose_b": ((0.10, 0.25, 0.60), 0.1, 0.5),
        "hose_r": ((0.60, 0.12, 0.10), 0.1, 0.5),
        "floor": ((0.40, 0.41, 0.43), 0.0, 0.8),
        "tile": ((0.55, 0.56, 0.58), 0.3, 0.6),
        "cdu": ((0.85, 0.86, 0.86), 0.2, 0.5),
        "busway": ((0.62, 0.64, 0.68), 0.85, 0.35),
        "glass": ((0.55, 0.65, 0.72), 0.0, 0.1),
        "meter": ((0.12, 0.13, 0.15), 0.3, 0.4),
        "yellow": ((0.85, 0.70, 0.10), 0.2, 0.5),
        "concrete": ((0.50, 0.49, 0.47), 0.0, 0.9),
    }
    for k, (c, mt, r) in new.items():
        m[k] = mat(f"rk_{k}", c, metal=mt, rough=r)
    glows = {
        "led_g": ((0.30, 1.0, 0.45), 4.0),
        "led_b": ((0.30, 0.65, 1.0), 4.0),
        "led_r": ((1.0, 0.20, 0.12), 4.0),
        "cold_b": ((0.30, 0.70, 1.0), 4.0),
        "hot_r": ((1.0, 0.35, 0.12), 4.0),
        "kw": ((1.0, 0.75, 0.25), 3.0),
        "kw_lo": ((0.40, 0.90, 0.55), 3.0),
        "nvl": ((0.45, 1.0, 0.55), 4.0),
        "data": ((0.85, 0.55, 1.0), 4.0),
    }
    for k, (c, s) in glows.items():
        m[k] = mat(f"rk_{k}", c, emit=c, strength=s)


def W(o, face, p):
    """Local rack point -> world (rack at o, facing +z when face = 1, -z when face = -1)."""
    return (o[0] + face * p[0], p[1], o[1] + face * p[2])


def _group(name, parent, o, face):
    g = empty(name, parent, P(o[0], 0.0, o[1]))
    if face < 0:
        g.rotation_euler = (0.0, 0.0, math.pi)
    return g


def _shell(m, g, name, cut, h=RH):
    parts = [
        fb(f"{name}_post0", (-RW, 0, RD - 3), (-RW + 3, h, RD), m["frame"], g),
        fb(f"{name}_post1", (RW - 3, 0, RD - 3), (RW, h, RD), m["frame"], g),
        fb(f"{name}_post2", (-RW, 0, -RD), (-RW + 3, h, -RD + 3), m["frame"], g),
        fb(f"{name}_post3", (RW - 3, 0, -RD), (RW, h, -RD + 3), m["frame"], g),
        fb(f"{name}_top", (-RW, h - 3, -RD), (RW, h, RD), m["frame"], g),
        fb(f"{name}_base", (-RW, 0, -RD), (RW, 4, RD), m["frame"], g),
        fb(f"{name}_side_l", (-RW, 4, -RD + 3), (-RW + 0.6, h - 3, RD - 3), m["frame2"], g),
    ]
    if not cut:
        parts.append(fb(f"{name}_side_r", (RW - 0.6, 4, -RD + 3), (RW, h - 3, RD - 3), m["frame2"], g))
    for zc in (-RD + 8, RD - 8):  # casters
        for xc in (-RW + 6, RW - 6):
            parts.append(fb(f"{name}_wh{zc}{xc}", (xc - 2, -6, zc - 2), (xc + 2, 0, zc + 2), m["rubber"], g))
    return parts


def rack_ai(m, parent, name, o=(0.0, 0.0), face=1, cut=True, liquid=True, slots=None):
    """An NVL72-class rack. cut: the +x side panel is off so trays show their insides. Returns
    (group, pts, glows) with world points and glow groups (leds, gpus)."""
    g = _group(name, parent, o, face)
    parts_t = []
    parts = _shell(m, g, name, cut)
    leds = empty(f"{name}_leds", g)
    gpus = empty(f"{name}_gpus", g)
    lp, gp = [], []
    trays = []
    for i, kd in enumerate(LAYOUT):
        if slots is not None and i not in slots:
            continue
        y = slot_y(i)
        bez = {"shelf": "bezel_p", "compute": "bezel_c", "switch": "bezel_s", "net": "bezel_s"}[kd]
        parts.append(fb(f"{name}_bz{i}", (-RW + 3, y + 0.3, RD - 4), (RW - 3, y + U - 0.3, RD - 2), m[bez], g))
        parts.append(fb(f"{name}_ch{i}", (-RW + 3.5, y + 0.3, -RD + 6), (RW - 3.5, y + 0.8, RD - 4), m["tray"], g))
        if kd == "compute":
            parts.append(fb(f"{name}_pcb{i}", (-RW + 5, y + 0.8, -RD + 10), (RW - 5, y + 1.1, RD - 8), m["pcb_g"], g))
            for k, (xc, zc) in enumerate(((-12, 14), (12, 14), (-12, -8), (12, -8))):
                parts.append(fb(f"{name}_cp{i}{k}", (xc - 6, y + 1.1, zc - 6), (xc + 6, y + 3.0, zc + 6), m["coldp"], g))
                gp.append(fb(f"{name}_gd{i}{k}", (xc - 4, y + 3.0, zc - 4), (xc + 4, y + 3.3, zc + 4), m["die_hot"], gpus))
            for k, xc in enumerate((-12, 12)):  # Grace CPUs
                parts.append(fb(f"{name}_cpu{i}{k}", (xc - 4, y + 1.1, 28), (xc + 4, y + 2.6, 36), m["coldp"], g))
            if liquid:
                for xc, mh in ((-20, "hose_b"), (20, "hose_r")):
                    parts.append(fb(f"{name}_hs{i}{xc}", (xc - 0.7, y + 1.4, -RD + 6), (xc + 0.7, y + 2.8, 20), m[mh], g))
            for k in range(6):
                parts.append(fb(f"{name}_fan{i}{k}", (-24 + k * 9.5 - 3.5, y + 0.9, RD - 2), (-24 + k * 9.5 + 3.5, y + U - 0.9, RD - 1.6), m["grill"], g))
            lp.append(fb(f"{name}_led{i}", (RW - 8, y + 1.5, RD - 2), (RW - 5.5, y + 2.8, RD - 1.4), m["led_g"], leds))
        elif kd == "switch":
            parts.append(fb(f"{name}_sw{i}", (-10, y + 0.8, -10), (10, y + 2.6, 10), m["coldp"], g))
            for k in range(18):
                parts.append(fb(f"{name}_port{i}{k}", (-26 + k * 2.9, y + 1.0, -RD + 3), (-24.6 + k * 2.9, y + U - 1.0, -RD + 6), m["gold"], g))
            lp.append(fb(f"{name}_led{i}", (RW - 8, y + 1.5, RD - 2), (RW - 5.5, y + 2.8, RD - 1.4), m["led_b"], leds))
        elif kd == "shelf":
            for k in range(6):
                xc = -22 + k * 8.8
                parts.append(fb(f"{name}_psu{i}{k}", (xc - 3.8, y + 0.8, -RD + 10), (xc + 3.8, y + U - 0.6, RD - 4), m["alu"], g))
                parts.append(fb(f"{name}_pf{i}{k}", (xc - 3, y + 0.9, RD - 2), (xc + 3, y + U - 0.9, RD - 1.6), m["grill"], g))
        else:
            for k in range(16):
                parts.append(fb(f"{name}_qs{i}{k}", (-26 + k * 3.2, y + 1.0, RD - 2), (-24.4 + k * 3.2, y + U - 1.0, RD - 1.4), m["gold"], g))
        trays.append((i, kd, y))
    # rear: NVLink spine cartridges (copper cable bundles), 50 V busbar, coolant manifolds
    yb0, yb1 = slot_y(0), slot_y(len(LAYOUT) - 1)
    for k, xc in enumerate((-6, -2, 2, 6)):
        parts.append(fb(f"{name}_spine{k}", (xc - 1.2, yb0 + 18, -RD + 3.2), (xc + 1.2, yb1 - 18, -RD + 6), m["copper"], g))
    parts.append(fb(f"{name}_bus", (10, yb0, -RD + 3.2), (13, yb1, -RD + 5.5), m["copper"], g))
    if liquid:
        for xc, mh in ((-20, "hose_b"), (20, "hose_r")):
            parts.append(fb(f"{name}_man{xc}", (xc - 2, 6, -RD + 2), (xc + 2, yb1 + 4, -RD + 6), m[mh], g))
    flush(name)
    pts = {
        "top": W(o, face, (0, RH + 4, 0)),
        "front": W(o, face, (0, 100, RD + 2)),
        "rear": W(o, face, (0, 100, -RD - 2)),
        "side": W(o, face, (RW, 100, 0)),
        "shelf": W(o, face, (RW, slot_y(1), 10)),
        "shelf_t": W(o, face, (RW, slot_y(33), 10)),
        "compute": W(o, face, (RW, slot_y(8), 14)),
        "switch": W(o, face, (RW, slot_y(18), 0)),
        "bus_top": W(o, face, (11.5, yb1, -RD + 4)),
        "bus_bot": W(o, face, (11.5, yb0, -RD + 4)),
        "man_b": W(o, face, (-20, 6, -RD + 4)),
        "man_r": W(o, face, (20, 6, -RD + 4)),
        "man_top": yb1,
        "trays": trays,
    }
    return g, pts, {"leds": leds, "gpus": gpus}


def rack_ent(m, parent, name, o=(0.0, 0.0), face=1, kind="srv", h=RH):
    """An air-cooled rack, front facing +z (face 1): 2U servers with fan grills and blanking
    panels (kind 'srv'), switches ('net') or disk shelves ('disk')."""
    g = _group(name, parent, o, face)
    parts_t = []
    parts = _shell(m, g, name, False, h)
    parts.append(fb(f"{name}_door", (-RW + 1, 5, RD - 1.5), (RW - 1, h - 4, RD - 1.0), m["grill"], g))
    leds = empty(f"{name}_leds", g)
    lp = []
    y = Y0 + 2
    n = 0
    step = 2 * U if kind != "net" else U
    while y + step < h - 10:
        if kind == "srv" and n % 3 == 2:
            parts.append(fb(f"{name}_bl{n}", (-RW + 3, y + 0.2, RD - 3), (RW - 3, y + step - 0.2, RD - 0.9), m["blank"], g))
        else:
            parts.append(fb(f"{name}_s{n}", (-RW + 3, y + 0.2, RD - 3), (RW - 3, y + step - 0.2, RD - 0.9), m["srv" if kind != "net" else "bezel_s"], g))
            if kind == "srv":
                for k in range(5):
                    parts.append(fb(f"{name}_f{n}{k}", (-22 + k * 9 - 3.2, y + 1.4, RD - 0.9), (-22 + k * 9 + 3.2, y + step - 1.4, RD - 0.6), m["grill"], g))
            elif kind == "disk":
                for k in range(12):
                    parts.append(fb(f"{name}_d{n}{k}", (-26 + k * 4.4, y + 0.8, RD - 0.9), (-22.6 + k * 4.4, y + step - 0.8, RD - 0.6), m["frame2"], g))
            else:
                for k in range(20):
                    parts.append(fb(f"{name}_p{n}{k}", (-26 + k * 2.6, y + 1.2, RD - 0.9), (-24.6 + k * 2.6, y + step - 1.2, RD - 0.6), m["gold"], g))
            lp.append(fb(f"{name}_l{n}", (RW - 6, y + 1.2, RD - 0.9), (RW - 4, y + 2.4, RD - 0.4), m["led_g" if kind != "net" else "led_b"], leds))
        y += step
        n += 1
    flush(name)
    pts = {"top": W(o, face, (0, h + 4, 0)), "front": W(o, face, (0, h * 0.5, RD + 1)),
           "rear": W(o, face, (0, h * 0.5, -RD - 1))}
    return g, pts, {"leds": leds}


def cdu(m, parent, name, o, face=1):
    """A coolant distribution unit: rack-sized cabinet, front door off: two pumps, a plate heat
    exchanger, supply (blue) and return (red) headers. Returns world points."""
    g = _group(name, parent, o, face)
    parts_t = []
    parts = _shell(m, g, name, True)
    parts.append(fb(f"{name}_skin", (-RW + 0.6, 4, -RD + 3), (RW - 0.6, RH - 3, -RD + 4), m["cdu"], g))
    for k, yc in enumerate((30.0, 70.0)):
        parts_t.append(D.tube(f"{name}_pump{k}", (-10, yc, 0), (14, yc, 0), 9.0, m["hose_b"], g, 20))
        parts_t.append(D.tube(f"{name}_motor{k}", (14, yc, 0), (26, yc, 0), 7.0, m["steel"], g, 20))
    parts.append(fb(f"{name}_hx", (-20, 100, -30), (20, 170, 30), m["steel"], g))
    for k in range(14):
        parts.append(fb(f"{name}_pl{k}", (-21, 104 + k * 4.6, -31), (21, 105 + k * 4.6, 31), m["alu"], g))
    parts.append(fb(f"{name}_scr", (-14, 180, RD - 2), (14, 196, RD - 1), m["screen"], g))
    flush(name)
    return {"top": W(o, face, (0, RH, 0)), "pump": W(o, face, (0, 50, 0)), "hx": W(o, face, (0, 135, 0)),
            "out": W(o, face, (-15, RH, -40)), "in": W(o, face, (15, RH, -40))}


def meter(m, parent, name, x, z, frac, mt):
    """A glowing kW column: dark glass tube 200 tall, filled to `frac`. Returns (fill group, top)."""
    fb(f"{name}_tube", (x - 5, 0, z - 5), (x + 5, 200, z + 5), m["meter"], parent)
    for k in range(11):
        fb(f"{name}_tick{k}", (x - 7, k * 20 - 0.3, z + 5), (x + 7, k * 20 + 0.3, z + 5.4), m["ink"], parent)
    fill = empty(f"{name}_fill", parent)
    fb(f"{name}_f", (x - 3.5, 0.5, z + 5), (x + 3.5, max(1.5, 200 * frac), z + 5.6), m[mt], fill)
    return fill, (x, 200 * frac + 4, z + 6)


def floor(m, parent, x0, x1, z0, z1, tiles=True, name="floor"):
    fb(f"{name}_slab", (x0, -12, z0), (x1, -6, z1), m["concrete"], parent)
    if tiles:
        fb(f"{name}_top", (x0, -6.6, z0), (x1, -6.0, z1), m["tile"], parent)
        lines = []
        x = x0
        while x <= x1:
            lines.append(fb(f"{name}_gx{x:.0f}", (x - 0.4, -6.0, z0), (x + 0.4, -5.8, z1), m["grid"], parent))
            x += 60.0
        z = z0
        while z <= z1:
            lines.append(fb(f"{name}_gz{z:.0f}", (x0, -6.0, z - 0.4), (x1, -5.8, z + 0.4), m["grid"], parent))
            z += 60.0
        flush(name)


# ---- the scene --------------------------------------------------------------------------------

ENT = (-110.0, 0.0)
AI = (0.0, 0.0)
CDU = (90.0, -200.0)
ROW_X0, ROW_Z = 260.0, 0.0  # the row of 13 old racks for beat 4


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    floor(m, root, -200, 1100, -150, 160)
    _, ep, eg = rack_ent(m, root, "ent", ENT)
    _, ap, ag = rack_ai(m, root, "ai", AI)
    cp = cdu(m, root, "cdu", CDU)
    fe, fe_top = meter(m, root, "m_ent", ENT[0] - 45, 75, 10 / 130 * 0.95, "kw_lo")
    fa, fa_top = meter(m, root, "m_ai", -45 + 4, 75, 0.95, "kw")
    show(fe, [(F(0, 0.15), F(1, 0)), (F(4, 0), F(5, 0))])
    show(fa, [(F(0, 0.35), F(1, 0)), (F(4, 0), F(5, 0))])
    show(ag["gpus"], [(F(1, 0.3), F(3, 0))])

    # overhead busway with tap boxes, whips down to each rack
    BY = 245.0
    bx("bw", (-200, BY, -70), (1100, BY + 10, -55), m["busway"], root)
    for k, x in enumerate((ENT[0], AI[0])):
        bx(f"tap{k}", (x - 8, BY - 16, -72), (x + 8, BY, -53), m["yellow"], root)
        D.polyline(f"whip{k}", [(x, BY - 16, -62), (x, RH + 2, -62), (x, RH, -50)], 1.4, m["rubber"], root)
    for i in range(13):
        x = ROW_X0 + i * 62
        bx(f"tapr{i}", (x - 6, BY - 12, -70), (x + 6, BY, -55), m["yellow"], root)
    # beat 0 + 3: power beads: few into the old rack, a stream into the AI rack
    run(root, "pw_e", [(-200, BY + 5, -62), (ENT[0], BY + 5, -62), (ENT[0], RH + 2, -62)], 2, 2.2, m["kw_lo"], [0, 3], 0.1, 0.8, 40)
    run(root, "pw_a", [(-200, BY + 5, -62), (AI[0], BY + 5, -62), (AI[0], RH + 2, -62)], 14, 2.2, m["kw"], [0, 3], 0.05, 0.85, 40)
    run(root, "bus_a", [ap["bus_top"], ap["bus_bot"]], 12, 1.4, m["kw"], [3], 0.15, 0.85, 50)

    # beat 1: NVLink chatter between compute and switch trays (on the cut side)
    xs = RW + 1.5
    for k in range(6):
        yc = slot_y(5 + k * 4 if k < 3 else 24 + (k - 3) * 3)
        ys = slot_y(15 + k)
        run(root, f"nvl{k}", [(xs, yc + 2, 10), (xs + 3, (yc + ys) / 2, -20), (xs, ys + 2, -50)], 3, 1.0, m["nvl"], [1], 0.1 + 0.05 * k, 0.8, 30)
    blink(ag["leds"], 1, [0, 2, 4, 6], n=8, on=0.6)

    # beat 2: air through the old rack, liquid through the AI rack
    for k in range(5):
        yy = 30 + k * 35
        run(root, f"air_in{k}", [(ENT[0] - 10 + k * 5, yy, 130), (ENT[0], yy, RD + 2)], 3, 1.6, m["cold_b"], [2], 0.0, 0.7, 30)
        run(root, f"air_out{k}", [(ENT[0], yy, -RD - 2), (ENT[0], yy + 20, -110), (ENT[0], yy + 50, -130)], 3, 1.6, m["hot_r"], [2], 0.1, 0.8, 30)
    sup = [cp["out"], (cp["out"][0], RH + 18, cp["out"][2]), (ap["man_b"][0], RH + 18, cp["out"][2]), (ap["man_b"][0], RH + 18, -RD + 4), (ap["man_b"][0], 10, -RD + 4)]
    ret = [(ap["man_r"][0], 10, -RD + 4), (ap["man_r"][0], RH + 12, -RD + 4), (ap["man_r"][0], RH + 12, cp["in"][2]), (cp["in"][0], RH + 12, cp["in"][2]), cp["in"]]
    D.polyline("pipe_s", [(p[0], p[1], p[2]) for p in sup[:4]], 2.4, m["hose_b"], root)
    D.polyline("pipe_r", [(p[0], p[1], p[2]) for p in ret[1:]], 2.4, m["hose_r"], root)
    run(root, "cool_s", sup, 12, 1.8, m["cold_b"], [2], 0.0, 0.8, 60)
    run(root, "cool_r", ret, 12, 1.8, m["hot_r"], [2], 0.1, 0.9, 60)
    for k, (i, kd, y) in enumerate([t for t in ap["trays"] if t[1] == "compute"][::3]):
        run(root, f"tray_c{k}", [(RW - 10, y + 2.1, -RD + 6), (RW - 10, y + 2.1, 20)], 2, 0.9, m["cold_b"], [2], 0.2, 0.7, 25)
        run(root, f"tray_h{k}", [(RW - 10, y + 2.1, 20), (RW - 10, y + 2.1, -RD + 6)], 2, 0.9, m["hot_r"], [2], 0.35, 0.85, 25)
    rise(root, "heat_e", (ENT[0], RH + 4, -RD), 6, 1.6, m["heat"], 2, 0.2, 0.9, 35.0, 50, (20.0, 10.0))

    # beat 3: weight on the floor
    for k, (xc, zc) in enumerate(((-RW + 6, RD - 8), (RW - 6, RD - 8), (-RW + 6, -RD + 8), (RW - 6, -RD + 8))):
        run(root, f"wt{k}", [(xc, 30, zc + 2), (xc, -4, zc + 2)], 3, 1.6, m["warn"], [3], 0.1, 0.8, 30)

    # beat 4: the row of 13 old racks, each a dim 10 kW meter sliver; one AI rack equals all
    row = empty("row", root)
    for i in range(13):
        rack_ent(m, row, f"old{i}", (ROW_X0 + i * 62, ROW_Z), 1, "srv" if i % 4 else "disk")
        bx(f"oldkw{i}", (ROW_X0 + i * 62 - 20, 0.5, 78), (ROW_X0 + i * 62 + 20, 15.0, 80), m["kw_lo"], row)
    run(root, "pw_row", [(-200, BY + 5, -62), (ROW_X0 + 12 * 62, BY + 5, -62)], 20, 2.0, m["kw_lo"], [4], 0.0, 0.8, 60)

    C.tags(root, {
        0: [("enterprise rack: ~10 kW", ep["top"]), ("NVL72 AI rack: ~130 kW", ap["top"]),
            ("kW meter", fa_top)],
        1: [("power shelves (AC -> 50 V DC)", ap["shelf"]), ("18 compute trays, 72 GPUs", ap["compute"]),
            ("9 NVLink switch trays", ap["switch"]), ("cold plate on every GPU", W(AI, 1, (RW, slot_y(26), 14)))],
        2: [("air: cool in front, hot out back", ep["rear"]), ("CDU: pumps + heat exchanger", cp["top"]),
            ("blue supply, red return", (AI[0] - 20, RH + 18, -100)), ("manifolds at the rack's back", ap["rear"])],
        3: [("overhead busway + tap box", (AI[0], BY, -62)), ("50 V busbar down the back", ap["bus_top"]),
            ("~1.4 t on four casters", (AI[0], 0, RD))],
        4: [("13 old racks = 130 kW", (ROW_X0 + 6 * 62, RH + 4, 0)), ("one AI rack = 130 kW", ap["top"]),
            ("NVDA, SMCI, VRT, EQIX", (ROW_X0 + 2 * 62, RH + 30, 0))],
    })
    C.done(SLUG, BEATS, [
        frame((-60.0, 105.0, 20.0), 300.0, 0.35, 0.18),
        frame((10.0, 95.0, 0.0), 210.0, 1.05, 0.10),
        [(0.0, frame((20.0, 120.0, -100.0), 380.0, 0.70, 0.35)), (0.5, frame((40.0, 140.0, -120.0), 320.0, 2.0, 0.30))],
        frame((0.0, 130.0, -20.0), 300.0, -2.5, 0.12),
        frame((420.0, 110.0, 0.0), 1000.0, 0.15, 0.22, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
