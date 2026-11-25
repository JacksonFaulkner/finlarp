"""Part builders for the NETWORK+COOL tab's CHILLER page (net_chiller_*.py), and the shared helpers the
COOLING TOWER page (net_cooling_tower_*.py) reuses.

The site scene is the TRM_CHILLER term's (terms/trm_chiller.py, imported, not edited): a data hall cut
open at z = 0 with two rack rows and an air handler, and an air-cooled chiller beside it, its skin cut
away: shell-and-tube evaporator, screw compressor + motor, expansion valve, V-bank condenser coils,
four fans on the deck and a free-cooling coil on the back. Units are centimetres, Y up, z toward the
camera.

Close-ups are built high above the site at BY so a section can show one part large:

  cycle_bench   the four-part refrigeration loop drawn big: evaporator (bottom) and condenser (top)
                shells cut open with their tube bundles, compressor (right), expansion valve (left)
  screw_bench   a twin-screw compressor, housing cut away: male and female helical rotors
  centri_bench  a centrifugal compressor: impeller with backswept blades, volute, magnetic bearings
  dry_bench     a V-bank dry cooler: two slanted finned coils, fans on top, adiabatic pads
  bars          a row of labelled bars (COP, temperatures, litres) for the number sections

Colours: blue = chilled water, amber = warm return water, cyan = cold refrigerant, red = hot gas.
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "terms")]
from sand_overview import F, P, beat, empty, label, show, tube, mat  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import present, bx, frame, camera_path, run, rise, blink, polyline  # noqa: E402
import term_common as C  # noqa: E402
import trm_chiller as CH  # noqa: E402

PAGE = "net_chiller"
BY = 700.0  # close-ups sit this high above the site


def setup(name, beats, page=PAGE):
    m, root = start(name, beats=beats, page=page)
    m.update(D.materials())
    for k, (c, metal, rough) in {
        "steel": ((0.60, 0.62, 0.66), 0.9, 0.35),
        "white": ((0.92, 0.92, 0.90), 0.0, 0.6),
        "brass": ((0.78, 0.62, 0.30), 0.9, 0.3),
        "rubber": ((0.10, 0.10, 0.11), 0.0, 0.85),
        "pad": ((0.62, 0.52, 0.34), 0.0, 0.9),
    }.items():
        m[k] = mat(f"n_{k}", c, metal=metal, rough=rough)
    m["warn"] = mat("n_warn", (1.0, 0.25, 0.15), emit=(1.0, 0.25, 0.15), strength=4.0)
    m["bar_b"] = mat("n_bar_b", (0.25, 0.55, 0.95), emit=(0.25, 0.55, 0.95), strength=1.2)
    m["bar_a"] = mat("n_bar_a", (0.95, 0.55, 0.18), emit=(0.95, 0.55, 0.18), strength=1.2)
    m["bar_g"] = mat("n_bar_g", (0.30, 0.85, 0.45), emit=(0.30, 0.85, 0.45), strength=1.2)
    m["bar_r"] = mat("n_bar_r", (0.95, 0.25, 0.18), emit=(0.95, 0.25, 0.18), strength=1.2)
    CH.mats(m)
    return m, root


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


# ---- the site (TRM_CHILLER's hall + chiller) ----------------------------------------------------

FANS = [(CH.CX0 + 40.0 + 73.0 * k, CH.CY1, -60.0) for k in range(4)]
FREE = [(CH.CX0 - 10.0, CH.EV[2] - 8.0, CH.EV[3]), (CH.CX0 + 12.0, 74.0, CH.CZ0 + 9.0), (CH.CX1 - 12.0, 86.0, CH.CZ0 + 9.0),
        (CH.CX1 - 12.0, 100.0, CH.CZ0 + 9.0), (CH.CX0 + 12.0, 112.0, CH.CZ0 + 9.0)]


def scene(m, root):
    leds = CH.hall(m, root)
    p = CH.chiller(m, root)
    fans = [CH.fan(m, root, f"fan{k}", c) for k, c in enumerate(FANS)]
    # boiling inside the evaporator shell: a group of small bubbles shown per beat by the caller
    return {"p": p, "fans": fans, "leds": leds}


def water(m, root, s, beats, n=12):
    run(root, "w_sup", s["p"]["sup"], n, 5.5, m["c_supply"], beats, 0.0, 0.7, 70)
    run(root, "w_ret", s["p"]["ret"], n, 5.5, m["c_return"], beats, 0.0, 0.7, 70)


def refrigerant(m, root, s, beats, parts=("suc", "dis", "liq")):
    p = s["p"]
    if "suc" in parts:
        run(root, "r_suc", p["suc"], 6, 3.6, m["r_cold"], beats, 0.05, 0.6, 40)
    if "dis" in parts:
        run(root, "r_dis", p["dis"], 7, 3.4, m["r_hot"], beats, 0.1, 0.65, 45)
    if "liq" in parts:
        run(root, "r_liq", p["liq"], 7, 3.0, m["r_cold"], beats, 0.15, 0.7, 50)


def boil(m, root, beats, name="boil"):
    x0, x1, ey, ez, er = CH.EV
    for k in range(5):
        rise(root, f"{name}{k}", (x0 + 15.0 + 27.0 * k, ey - 12.0, ez + 6.0), 3, 1.4, m["r_cold"], beats, 0.0 + 0.04 * k, 0.85,
             22.0, 30, (6.0, 4.0))


def fans_spin(s, beats, turns=3.0):
    for f_ in s["fans"]:
        C.spin(f_, beats, turns=turns)


def plumes(m, root, beats, n=8, h=90.0, name="plume"):
    for k, c in enumerate(FANS):
        rise(root, f"{name}{k}", (c[0], c[1] + 10.0, c[2]), n, 3.6, m["heat"], beats, 0.0, 0.85, h, 50, (14.0, 14.0))


def comp_heat(m, root, beats):
    rise(root, "cmp_heat", (CH.CMP[0] + 20.0, CH.CMP[2] + 18.0, CH.CMP[3] + 6.0), 5, 1.6, m["heat"], beats, 0.2, 0.8, 20.0, 40,
         (10.0, 4.0))


EVAP_TAG = (CH.EV[0] + 40.0, CH.EV[2] + CH.EV[4], 0.0)
COMP_TAG = (CH.CMP[0] + 20.0, CH.CMP[2] + 18.0, -50.0)
COND_TAG = (120.0, 100.0, -25.0)
VALVE_TAG = (210.0, 62.0, -35.0)
FAN_TAG = (CH.CX0 + 113.0, CH.CY1 + 20.0, -60.0)
HALL_TAG = (-200.0, 215.0, -110.0)
AHU_TAG = (-90.0, 225.0, -130.0)
FREE_TAG = (CH.CX0 + 140.0, 100.0, CH.CZ0 + 9.0)
SITE = frame((0.0, 60.0, -120.0), 680.0, 0.25, 0.40, pad=1.0)
UNIT = frame((180.0, 60.0, -55.0), 300.0, 0.15, 0.22)


# ---- shared shapes --------------------------------------------------------------------------------


def half_shell(name, x0, x1, y, z, r, mt, g, n=20):
    """The back half of a horizontal cylinder along x, so what is inside shows from the front."""
    parts = []
    for j in range(n):
        a0, a1 = math.pi * j / n, math.pi * (j + 1) / n
        y0, z0 = y + r * math.cos(a0), z - r * math.sin(a0)
        y1, z1 = y + r * math.cos(a1), z - r * math.sin(a1)
        parts.append(bx(f"{name}{j}", (x0, min(y0, y1), min(z0, z1) - 0.8), (x1, max(y0, y1) + 0.8, max(z0, z1)), mt, g))
    return D.join(parts, f"{name}_m")


def bundle(name, x0, x1, y, z, mt, g, n=4, pitch=8.0, r=1.6):
    parts = []
    for i in range(n):
        for j in range(n):
            yy, zz = y - pitch * (n - 1) / 2 + pitch * i, z - pitch * (n - 1) / 2 + pitch * j
            parts.append(tube(f"{name}{i}{j}", (x0, yy, zz), (x1, yy, zz), r, mt, g, 8))
    return D.join(parts, f"{name}_m")


def bars(m, root, name, x0, y0, z, items, w=26.0, gap=14.0, unit=1.0):
    """Bars side by side from (x0, y0); items are (value, material key, text). Returns the group and
    each bar's top (for its tag)."""
    g = empty(name, root)
    tops = []
    bx(f"{name}_base", (x0 - 10.0, y0 - 3.0, z - 16.0), (x0 + len(items) * (w + gap) + 0.0, y0, z + 4.0), m["frame"], g)
    for k, (v, mk, _t) in enumerate(items):
        xa = x0 + k * (w + gap)
        h = max(2.0, v * unit)
        bx(f"{name}_{k}", (xa, y0, z - 12.0), (xa + w, y0 + h, z), m[mk], g)
        tops.append((xa + w / 2, y0 + h + 4.0, z))
    return g, tops


# ---- close-ups ------------------------------------------------------------------------------------

CB = (0.0, BY, -60.0)  # cycle bench centre
EVY, CDY = BY - 80.0, BY + 80.0
SHX = (-120.0, 120.0)
SHR = 30.0
CPX, XVX = 175.0, -175.0


def cycle_bench(m, root, name="cyc"):
    """The refrigeration loop, big: evaporator below, condenser above, compressor right, valve left."""
    g = empty(name, root)
    z = CB[2]
    for nm, y, shm in (("ev", EVY, m["shell"]), ("cd", CDY, m["pipe_r"])):
        half_shell(f"{name}_{nm}sh", SHX[0], SHX[1], y, z, SHR, shm, g)
        for xe in (SHX[0] - 8.0, SHX[1]):
            tube(f"{name}_{nm}hd{xe:.0f}", (xe, y, z), (xe + 8.0, y, z), SHR + 3.0, shm, g, 24)
        bundle(f"{name}_{nm}b", SHX[0], SHX[1], y, z, m["copper"], g, n=4, pitch=11.0, r=2.4)
        for xs in (SHX[0] + 30.0, SHX[1] - 30.0):
            bx(f"{name}_{nm}sd{xs:.0f}", (xs - 8.0, y - SHR - 14.0, z - 20.0), (xs + 8.0, y - SHR + 4.0, z + 20.0), m["frame"], g)
    # compressor: housing + motor standing on the right
    tube(f"{name}_cmp", (CPX, BY - 40.0, z), (CPX, BY + 20.0, z), 26.0, m["steel"], g, 24)
    tube(f"{name}_mot", (CPX, BY + 20.0, z), (CPX, BY + 56.0, z), 22.0, m["motor"], g, 24)
    for k in range(6):
        tube(f"{name}_rib{k}", (CPX, BY + 24.0 + 5.0 * k, z), (CPX, BY + 25.5 + 5.0 * k, z), 23.5, m["motor"], g, 24)
    # expansion valve: brass body, bonnet and a little wheel
    bx(f"{name}_xv", (XVX - 14.0, BY - 12.0, z - 14.0), (XVX + 14.0, BY + 12.0, z + 14.0), m["brass"], g)
    tube(f"{name}_xvb", (XVX, BY + 12.0, z), (XVX, BY + 30.0, z), 6.0, m["brass"], g, 12)
    tube(f"{name}_xvw", (XVX, BY + 30.0, z), (XVX, BY + 33.0, z), 14.0, m["dark"], g, 16)
    paths = {
        "suc": [(SHX[1] + 8.0, EVY + 14.0, z), (CPX, EVY + 14.0, z), (CPX, BY - 40.0, z)],
        "dis": [(CPX, BY + 56.0, z), (CPX, CDY + 14.0, z), (SHX[1] + 8.0, CDY + 14.0, z)],
        "liq": [(SHX[0] - 8.0, CDY - 14.0, z), (XVX, CDY - 14.0, z), (XVX, BY + 12.0, z)],
        "flash": [(XVX, BY - 12.0, z), (XVX, EVY - 14.0, z), (SHX[0] - 8.0, EVY - 14.0, z)],
        "ev_in": [(SHX[0] - 60.0, EVY, z + 2.0), (SHX[1] + 60.0, EVY, z + 2.0)],
        "cd_in": [(SHX[1] + 60.0, CDY, z + 2.0), (SHX[0] - 60.0, CDY, z + 2.0)],
    }
    for k in ("suc", "dis", "liq", "flash"):
        polyline(f"{name}_p{k}", paths[k], 4.5 if k != "liq" else 3.2, m["copper"], g)
    polyline(f"{name}_wev", paths["ev_in"], 5.0, m["pipe_s"], g)
    polyline(f"{name}_wcd", paths["cd_in"], 5.0, m["pipe_r"], g)
    return {"g": g, "paths": paths, "ev": (0.0, EVY + SHR + 6.0, z), "cd": (0.0, CDY + SHR + 6.0, z),
            "cmp": (CPX, BY + 60.0, z), "xv": (XVX, BY + 36.0, z)}


def cycle_flow(m, root, c, beats, which=("suc", "dis", "liq", "flash"), name="cy", u0=0.0, u1=0.8):
    mk = {"suc": "r_cold", "dis": "r_hot", "liq": "r_hot", "flash": "r_cold"}
    for k in which:
        run(root, f"{name}_{k}", c["paths"][k], 6, 4.0, m[mk[k]], beats, u0, u1, 40)


def cycle_water(m, root, c, beats, name="cyw"):
    z = CB[2] + 2.0
    run(root, f"{name}_e", [(SHX[0] - 60.0, EVY, z), (0.0, EVY, z)], 6, 4.5, m["c_return"], beats, 0.0, 0.5, 40)
    run(root, f"{name}_e2", [(0.0, EVY, z), (SHX[1] + 60.0, EVY, z)], 6, 4.5, m["c_supply"], beats, 0.08, 0.6, 40)
    run(root, f"{name}_c", [(SHX[1] + 60.0, CDY, z), (0.0, CDY, z)], 6, 4.5, m["c_supply"], beats, 0.0, 0.5, 40)
    run(root, f"{name}_c2", [(0.0, CDY, z), (SHX[0] - 60.0, CDY, z)], 6, 4.5, m["c_return"], beats, 0.08, 0.6, 40)


def cycle_boil(m, root, beats, name="cyb"):
    for k in range(7):
        rise(root, f"{name}{k}", (SHX[0] + 20.0 + 33.0 * k, EVY - 20.0, CB[2] + 8.0), 3, 2.2, m["r_cold"], beats, 0.03 * k, 0.85, 34.0,
             30, (8.0, 6.0))


def cycle_drip(m, root, beats, name="cyd"):
    for k in range(7):
        x = SHX[0] + 20.0 + 33.0 * k
        run(root, f"{name}{k}", [(x, CDY + 10.0, CB[2] + 8.0), (x, CDY - 26.0, CB[2] + 8.0)], 3, 2.0, m["r_hot"], beats, 0.03 * k, 0.85,
            24)


SB = (0.0, BY, -60.0)  # screw bench


def screw_bench(m, root, name="scr"):
    """Twin-screw compressor, top of the housing cut away: male (4 lobes) and female (6) rotors."""
    g = empty(name, root)
    x0, x1, y, z = -150.0, 150.0, BY, -60.0
    half_shell(f"{name}_h1", x0, x1, y, z - 22.0, 34.0, m["steel"], g)
    half_shell(f"{name}_h2", x0, x1, y, z + 22.0, 34.0, m["steel"], g)
    bx(f"{name}_flr", (x0, y - 36.0, z - 56.0), (x1, y - 30.0, z + 40.0), m["frame"], g)
    rot = []
    for k, (dz, lobes, r, hand) in enumerate(((-22.0, 4, 26.0, 1), (22.0, 6, 22.0, -1))):
        rot.append(tube(f"{name}_core{k}", (x0, y, z + dz), (x1, y, z + dz), r * 0.55, m["alu"], g, 16))
        for L in range(lobes):
            pts = []
            for s in range(41):
                xs = x0 + (x1 - x0) * s / 40
                a = 2 * math.pi * L / lobes + hand * 2.2 * math.pi * s / 40
                pts.append((xs, y + r * 0.8 * math.cos(a), z + dz + r * 0.8 * math.sin(a)))
            rot.append(polyline(f"{name}_lb{k}{L}", pts, r * 0.22, m["alu"], g))
    D.join(rot, f"{name}_rotors")
    tube(f"{name}_mot", (x1, y, z - 22.0), (x1 + 90.0, y, z - 22.0), 34.0, m["motor"], g, 24)
    tube(f"{name}_in", (x0 + 20.0, y + 30.0, z), (x0 + 20.0, y + 80.0, z), 16.0, m["copper"], g, 16)
    tube(f"{name}_out", (x1 - 20.0, y - 30.0, z), (x1 - 20.0, y - 80.0, z), 11.0, m["copper"], g, 16)
    return {"g": g, "in": (x0 + 20.0, y + 84.0, z), "out": (x1 - 20.0, y - 84.0, z), "mot": (x1 + 45.0, y + 36.0, z - 22.0),
            "rot": (0.0, y + 30.0, z)}


def screw_gas(m, root, beats, name="sg"):
    """Gas pockets ride the lobes from suction (left, cyan, spaced wide) to discharge (right, red,
    packed tight)."""
    x0, x1, y, z = -150.0, 150.0, BY, -60.0
    run(root, f"{name}_in", [(x0 + 20.0, y + 84.0, z), (x0 + 20.0, y + 14.0, z)], 6, 4.0, m["r_cold"], beats, 0.0, 0.6, 30)
    run(root, f"{name}_c", [(x0 + 20.0, y + 14.0, z), (-30.0, y + 10.0, z), (60.0, y + 4.0, z)], 8, 4.0, m["r_cold"], beats, 0.05, 0.7, 50)
    run(root, f"{name}_h", [(60.0, y + 4.0, z), (x1 - 20.0, y, z)], 8, 3.4, m["r_hot"], beats, 0.15, 0.85, 22)
    run(root, f"{name}_out", [(x1 - 20.0, y - 10.0, z), (x1 - 20.0, y - 84.0, z)], 8, 3.4, m["r_hot"], beats, 0.2, 0.9, 24)


def centri_bench(m, root, name="cen", c=(0.0, BY, -60.0)):
    """Centrifugal compressor: an impeller (disk + 12 backswept blades) in a volute, on a shaft held
    by magnetic bearings (glowing rings), with its motor behind."""
    g = empty(name, root)
    x, y, z = c
    imp = empty(f"{name}_imp", root, P(x, y, z))
    tube(f"{name}_disk", (0.0, 0.0, -6.0), (0.0, 0.0, -2.0), 60.0, m["alu"], imp, 40)
    tube(f"{name}_eye", (0.0, 0.0, -2.0), (0.0, 0.0, 14.0), 14.0, m["alu"], imp, 24)
    bl = []
    for k in range(12):
        a0 = 2 * math.pi * k / 12
        pts = []
        for s in range(9):
            r = 14.0 + 44.0 * s / 8
            a = a0 + 0.7 * s / 8
            pts.append((r * math.cos(a), r * math.sin(a), -2.0 + 10.0 * (1 - s / 8)))
        bl.append(polyline(f"{name}_bl{k}", pts, 2.0, m["alu"], imp))
    D.join(bl, f"{name}_blades")
    vol = []
    for j in range(48):
        a0, a1 = 2 * math.pi * j / 48, 2 * math.pi * (j + 1) / 48
        r0, r1 = 72.0 + 26.0 * j / 48, 72.0 + 26.0 * (j + 1) / 48
        vol.append(tube(f"{name}_v{j}", (x + r0 * math.cos(a0), y + r0 * math.sin(a0), z - 10.0),
                        (x + r1 * math.cos(a1), y + r1 * math.sin(a1), z - 10.0), 8.0 + 6.0 * j / 48, m["steel"], g, 10))
    D.join(vol, f"{name}_volute")
    tube(f"{name}_dis", (x + 98.0, y, z - 10.0), (x + 98.0, y + 110.0, z - 10.0), 16.0, m["copper"], g, 16)
    tube(f"{name}_shaft", (x, y, z - 6.0), (x, y, z - 150.0), 6.0, m["steel"], g, 16)
    brg = empty(f"{name}_brg", root)
    for k, zz in enumerate((z - 40.0, z - 110.0)):
        tube(f"{name}_mb{k}", (x, y, zz), (x, y, zz - 10.0), 16.0, m["field"], brg, 24)
    tube(f"{name}_mot", (x, y, z - 55.0), (x, y, z - 100.0), 30.0, m["motor"], g, 28)
    return {"g": g, "imp": imp, "brg": brg, "eye": (x, y, z + 14.0), "dis": (x + 98.0, y + 114.0, z - 10.0),
            "mb": (x, y + 18.0, z - 40.0), "mot": (x, y + 32.0, z - 78.0)}


def centri_gas(m, root, c, beats, name="cg"):
    x, y, z = c
    run(root, f"{name}_in", [(x, y, z + 80.0), (x, y, z + 6.0)], 6, 3.6, m["r_cold"], beats, 0.0, 0.7, 25)
    for k in range(6):
        a0 = 2 * math.pi * k / 6
        pts = [(x + (14.0 + 70.0 * s / 6) * math.cos(a0 + 1.4 * s / 6), y + (14.0 + 70.0 * s / 6) * math.sin(a0 + 1.4 * s / 6), z + 2.0)
               for s in range(7)]
        run(root, f"{name}_sp{k}", pts, 2, 3.4, m["r_hot"], beats, 0.05 + 0.05 * k, 0.85, 25)
    run(root, f"{name}_out", [(x + 98.0, y + 10.0, z - 10.0), (x + 98.0, y + 114.0, z - 10.0)], 6, 3.6, m["r_hot"], beats, 0.2, 0.9, 25)


DB = (0.0, BY, -100.0)  # dry cooler bench


def dry_bench(m, root, name="dry", c=DB):
    """A V-bank dry cooler: two finned coils leaning in, three fans on top, adiabatic pads outside the
    coils with water trickling down them."""
    g = empty(name, root)
    x, y, z = c
    L = 360.0
    x0, x1 = x - L / 2, x + L / 2
    bx(f"{name}_base", (x0, y - 6.0, z - 70.0), (x1, y, z + 70.0), m["frame"], g)
    for xe in (x0, x1 - 6.0):
        bx(f"{name}_end{xe:.0f}", (xe, y, z - 70.0), (xe + 6.0, y + 160.0, z + 70.0), m["skin"], g)
    coils, hot = [], empty(f"{name}_hot", root)
    for side in (-1, 1):
        for k in range(16):
            t = k / 15.0
            yy = y + 10.0 + 140.0 * t
            zz = z + side * (20.0 + 40.0 * t)
            coils.append(bx(f"{name}_c{side}{k}", (x0 + 6.0, yy, zz - 2.0), (x1 - 6.0, yy + 3.0, zz + 2.0), m["fin"], g))
            if k % 3 == 1:
                tube(f"{name}_h{side}{k}", (x0 + 8.0, yy + 1.5, zz + side * 2.5), (x1 - 8.0, yy + 1.5, zz + side * 2.5), 1.0,
                     m["coil_hot"], hot, 8)
    D.join(coils, f"{name}_coils")
    bx(f"{name}_deck", (x0, y + 157.0, z - 70.0), (x1, y + 160.0, z + 70.0), m["frame"], g)
    fans = [CH.fan(m, root, f"{name}_f{k}", (x0 + 60.0 + 120.0 * k, y + 160.0, z), r=46.0) for k in range(3)]
    pads = empty(f"{name}_pads", root)
    for side in (-1,):  # back pad only, so the coils stay in view from the front
        zz = z + side * 74.0
        bx(f"{name}_pad{side}", (x0 + 10.0, y + 10.0, zz - 3.0), (x1 - 10.0, y + 140.0, zz + 3.0), m["pad"], pads)
        tube(f"{name}_dist{side}", (x0 + 10.0, y + 144.0, zz), (x1 - 10.0, y + 144.0, zz), 3.0, m["pvc"] if "pvc" in m else m["white"],
             pads, 12)
    sup = [(x0 - 120.0, y + 30.0, z), (x0 + 10.0, y + 30.0, z), (x0 + 10.0, y + 30.0, z - 30.0), (x1 - 10.0, y + 140.0, z - 60.0)]
    ret = [(x1 - 10.0, y + 140.0, z + 60.0), (x0 + 14.0, y + 40.0, z + 30.0), (x0 + 14.0, y + 20.0, z + 10.0), (x0 - 120.0, y + 20.0, z + 10.0)]
    polyline(f"{name}_in", sup[:2], 6.0, m["pipe_r"], g)
    polyline(f"{name}_out", ret[2:], 6.0, m["pipe_s"], g)
    return {"g": g, "fans": fans, "hot": hot, "pads": pads, "sup": sup, "ret": ret, "top": (x, y + 175.0, z),
            "pad": (x, y + 100.0, z - 77.0), "coil": (x + 60.0, y + 90.0, z + 40.0), "c": c}


def dry_flow(m, root, d, beats, adiabatic=False, name="df"):
    x, y, z = d["c"]
    run(root, f"{name}_w", d["sup"], 8, 5.0, m["c_return"], beats, 0.0, 0.6, 60)
    run(root, f"{name}_r", d["ret"], 8, 5.0, m["c_supply"], beats, 0.2, 0.8, 60)
    for k, f_ in enumerate(d["fans"]):
        C.spin(f_, beats, turns=4.0)
        rise(root, f"{name}_pl{k}", (x - 120.0 + 120.0 * k, y + 170.0, z), 6, 4.0, m["heat"], beats, 0.0, 0.85, 90.0, 50, (25.0, 25.0))
    for side in (-1, 1):
        run(root, f"{name}_air{side}", [(x, y + 60.0, z + side * 160.0), (x, y + 70.0, z + side * 50.0), (x, y + 150.0, z)], 6, 3.2,
            m["air"] if "air" in m else m["cool"], beats, 0.0, 0.85, 45)
        if adiabatic and side < 0:
            for k in range(5):
                xx = x - 140.0 + 70.0 * k
                run(root, f"{name}_dr{side}{k}", [(xx, y + 140.0, z + side * 77.0), (xx, y + 12.0, z + side * 77.0)], 2, 2.4, m["c_supply"],
                    beats, 0.04 * k, 0.85, 30)
