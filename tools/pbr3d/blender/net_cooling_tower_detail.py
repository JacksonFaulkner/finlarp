"""Part builders for the NETWORK+COOL tab's COOLING TOWER page (net_cooling_tower_*.py). The page also
covers HEAT OUT: where the heat finally goes, into the outdoor air.

The site is the TRM_COOLING_TOWER term's (terms/trm_cooling_tower.py, imported, not edited): a
water-cooled chiller plant (condenser barrel, compressor, pump) on the left and an induced-draft,
counterflow wet cooling tower on the right, its front cut away at z = 0: basin, louvers, fill pack,
spray header + nozzles, drift eliminators, fan deck, fan stack, gearbox and motor, plus a make-up water
meter and a blowdown drain. Units are centimetres.

Close-ups above the site at BY (helpers from net_chiller_detail.py):
  fill_bench    four corrugated fill sheets, big: water films running down, air rising between them
  drift_bench   chevron drift-eliminator blades: droplets carried up and caught, vapour passing
  drop_bench    one falling water drop: vapour leaving its skin, the drop cooling as it falls
Water: amber = warm from the chiller, blue = cooled. White = vapour. Green = make-up water.
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "terms")]
import net_chiller_detail as N  # noqa: E402
from net_chiller_detail import F, P, beat, empty, show, tube, bx, frame, camera_path, run, rise, blink, polyline, present, C, D  # noqa: E402
import trm_cooling_tower as CT  # noqa: E402

PAGE = "net_cooling_tower"
BY = N.BY
TX0, TX1, TZ0 = CT.TX0, CT.TX1, CT.TZ0
FANC, DECK, SPRAY, FILL, DRIFT, LOUV = CT.FANC, CT.DECK, CT.SPRAY, CT.FILL, CT.DRIFT, CT.LOUV
span, tags, bars = N.span, N.tags, N.bars


def setup(name, beats):
    m, root = N.setup(name, beats, page=PAGE)
    CT.mats(m)
    return m, root


WARM = [(-95.0, 62.0, -90.0), (-10.0, 62.0, -90.0), (-10.0, SPRAY, -90.0), (TX0 - 30.0, SPRAY, -100.0), (TX1 - 12.0, SPRAY, -100.0)]
COOL = [(TX0 + 20.0, 12.0, -40.0), (-20.0, 12.0, -40.0), (-40.0, 20.0, -40.0), (-40.0, 30.0, -40.0), (-60.0, 30.0, -40.0),
        (-60.0, 38.0, -90.0), (-95.0, 38.0, -90.0)]
MK = [(TX1 + 80.0, 6.0, -40.0), (TX1 + 40.0, 6.0, -40.0), (TX1 + 40.0, 36.0, -40.0), (TX1 - 10.0, 36.0, -40.0)]
BD = [(TX0 + 10.0, 6.0, -20.0), (TX0 - 10.0, 6.0, -20.0), (TX0 - 10.0, 2.0, 20.0)]


def scene(m, root):
    """TRM_COOLING_TOWER's site, rebuilt from its parts."""
    leds = CT.plant(m, root)
    CT.tower(m, root)
    fh = CT.fan(m, root)
    polyline("cw_warm", WARM[:4], 5.0, m["pipe_r"], root)
    polyline("cw_cool", COOL, 5.0, m["pipe_s"], root)
    polyline("mk_line", MK, 2.6, m["copper"], root)
    meter = empty("mk_meter", root)
    bx("mk_body", (TX1 + 52.0, 0.0, -50.0), (TX1 + 70.0, 16.0, -30.0), m["brass"], meter)
    bx("mk_face", (TX1 + 54.0, 16.0, -48.0), (TX1 + 68.0, 17.0, -32.0), m["white"], meter)
    dial = empty("mk_dial", root, P(TX1 + 61.0, 17.2, -40.0))
    bx("mk_needle", (-0.4, 0.0, 0.0), (0.4, 0.4, -6.0), m["warn"], dial)
    polyline("bd_line", BD, 2.0, m["copper"], root)
    films = empty("films", root)
    for i in range(7):
        x = TX0 + 22.0 + 30.0 * i
        tube(f"film{i}", (x, SPRAY - 8.0, -4.0), (x, FILL[0], -4.0), 0.8, m["film"], films, 6)
    show(films, [])
    return {"leds": leds, "fan": fh, "dial": dial, "films": films}


def loop(m, root, beats, n=12):
    run(root, "w_warm", WARM, n, 5.5, m["c_return"], beats, 0.0, 0.7, 70)
    run(root, "w_cool", COOL, n, 5.5, m["c_supply"], beats, 0.0, 0.7, 70)


def falling(m, root, beats, name="drop"):
    for i in range(7):
        x = TX0 + 22.0 + 30.0 * i
        run(root, f"{name}_w{i}", [(x, SPRAY - 6.0, -4.0), (x, FILL[1], -4.0)], 2, 2.2, m["c_return"], beats, 0.0, 0.8, 14)
        run(root, f"{name}_c{i}", [(x + 3.0, FILL[0], -4.0), (x + 3.0, 32.0, -4.0)], 2, 2.2, m["c_supply"], beats, 0.1, 0.9, 18)


def spray(m, root, beats, name="spr"):
    run(root, f"{name}_h", [(TX0 - 30.0, SPRAY, -100.0), (TX1 - 12.0, SPRAY, -100.0)], 8, 3.4, m["c_return"], beats, 0.0, 0.6, 40)
    for i in range(7):
        x = TX0 + 22.0 + 30.0 * i
        run(root, f"{name}_a{i}", [(x, SPRAY, -100.0), (x, SPRAY, -8.0), (x, SPRAY - 8.0, -4.0)], 2, 2.4, m["c_return"], beats,
            0.2 + 0.03 * i, 0.85, 22)


def air(m, root, beats, name="air"):
    for s, x0 in ((-1, TX0 - 40.0), (1, TX1 + 40.0)):
        xm = TX0 + 50.0 if s < 0 else TX1 - 50.0
        run(root, f"{name}{s}", [(x0, 70.0, -4.0), (xm, 80.0, -4.0), (xm, FILL[1], -4.0), (FANC[0] + s * 30.0, DECK, -60.0),
                                 (FANC[0] + s * 30.0, DECK + 90.0, -60.0)], 8, 3.0, m["air"], beats, 0.0, 0.75, 70)


def plume(m, root, beats, n=18, h=140.0, name="plume"):
    rise(root, name, (FANC[0], DECK + 60.0, FANC[2]), n, 6.0, m["vapour"], beats, 0.0, 0.85, h, 70, (45.0, 45.0))


def makeup(m, root, s, beats):
    run(root, "mk_flow", MK, 8, 2.6, m["makeup"], beats, 0.0, 0.75, 45)
    run(root, "bd_flow", BD, 4, 2.2, m["c_supply"], beats, 0.2, 0.8, 30)
    C.spin(s["dial"], beats, turns=2.0)


def drift_drops(m, root, beats, name="dd"):
    """Droplets carried up from the spray hit the eliminators and fall back."""
    for i in range(6):
        x = TX0 + 30.0 + 36.0 * i
        run(root, f"{name}{i}", [(x, SPRAY + 2.0, -3.0), (x + 2.0, DRIFT[0] - 1.0, -3.0), (x - 2.0, SPRAY - 4.0, -3.0)], 2, 1.8,
            m["c_return"], beats, 0.05 * i, 0.85, 30)


PLANT_TAG = (-165.0, 90.0, -60.0)
TOWER_TAG = (TX1, DECK + 70.0, -60.0)
FILL_TAG = (FANC[0], FILL[1] - 10.0, -2.0)
SPRAY_TAG = (TX0 + 40.0, SPRAY, -8.0)
DRIFT_TAG = (TX1 - 40.0, DRIFT[1], -3.0)
LOUV_TAG = (TX0 - 4.0, 80.0, -4.0)
FAN_TAG = (FANC[0], DECK + 20.0, FANC[2])
SKY_TAG = (FANC[0], DECK + 160.0, FANC[2])
BASIN_TAG = (FANC[0] + 60.0, 32.0, -4.0)
METER_TAG = (TX1 + 61.0, 20.0, -40.0)
BD_TAG = (TX0 - 10.0, 6.0, 0.0)
SITE = frame((40.0, 130.0, -90.0), 600.0, 0.28, 0.30, pad=1.0)
TOWER = frame((FANC[0], 140.0, -60.0), 300.0, 0.10, 0.12)


# ---- close-ups ------------------------------------------------------------------------------------

FB = (0.0, BY, -40.0)


def fill_bench(m, root, name="fb"):
    """Four corrugated fill sheets, each a zig-zag in the (x, y) plane extruded along z."""
    g = empty(name, root)
    x0, y, z = FB
    sheets = []
    for i in range(4):
        x = -90.0 + 60.0 * i
        for j in range(8):
            ya = y - 120.0 + 30.0 * j
            xa, xb = x + (0.0 if j % 2 == 0 else 8.0), x + (8.0 if j % 2 == 0 else 0.0)
            for d in range(5):  # the corrugated sheet as ridges stepping back in z
                sheets.append(tube(f"{name}_e{i}{j}{d}", (xa, ya, z - 18.0 * d), (xb, ya + 30.0, z - 18.0 * d), 1.4 if d == 0 else 1.0,
                                   m["fillm"], g, 6))
            sheets.append(tube(f"{name}_r{i}{j}", (xa, ya, z), (xa, ya, z - 72.0), 0.8, m["fillm"], g, 6))
    D.join(sheets, f"{name}_edges")
    film = empty(f"{name}_film", root)
    for i in range(4):
        x = -90.0 + 60.0 * i
        pts = []
        for j in range(9):
            pts.append((x + (0.0 if j % 2 == 0 else 8.0) + 1.6, y - 120.0 + 30.0 * j, z + 1.2))
        polyline(f"{name}_fl{i}", list(reversed(pts)), 0.9, m["film"], film)
    return {"g": g, "film": film, "top": (0.0, y + 130.0, z), "sheet": (-90.0, y + 40.0, z), "gap": (-60.0, y, z),
            "bottom": (0.0, y - 130.0, z)}


def fill_flow(m, root, beats, name="ff"):
    x0, y, z = FB
    for i in range(4):
        x = -90.0 + 60.0 * i
        pts = [(x + (0.0 if j % 2 == 0 else 8.0) + 2.0, y + 120.0 - 30.0 * j, z + 2.0) for j in range(9)]
        half = pts[:5]
        run(root, f"{name}_w{i}", half, 3, 2.6, m["c_return"], beats, 0.05 * i, 0.6, 40)
        run(root, f"{name}_c{i}", pts[4:], 3, 2.6, m["c_supply"], beats, 0.1 + 0.05 * i, 0.75, 40)
        if i < 3:
            xg = x + 34.0
            run(root, f"{name}_a{i}", [(xg, y - 140.0, z + 2.0), (xg + 4.0, y, z + 2.0), (xg, y + 140.0, z + 2.0)], 4, 2.4, m["air"], beats,
                0.0, 0.8, 50)
            rise(root, f"{name}_v{i}", (xg, y - 40.0, z + 2.0), 4, 1.8, m["vapour"], beats, 0.1, 0.85, 120.0, 50, (6.0, 2.0))


DRB = (0.0, BY + 400.0, -40.0)


def drift_bench(m, root, name="drb"):
    g = empty(name, root)
    x0, y, z = DRB
    blades = []
    for i in range(7):
        x = -120.0 + 40.0 * i
        pts = [(x, y - 50.0, z), (x + 14.0, y - 15.0, z), (x, y + 15.0, z), (x + 14.0, y + 50.0, z)]
        for k in range(3):
            blades.append(tube(f"{name}_b{i}{k}", pts[k], pts[k + 1], 2.0, m["frp"], g, 6))
        bx(f"{name}_back{i}", (x - 1.0, y - 50.0, z - 70.0), (x + 15.0, y + 50.0, z - 68.0), m["frp"], g)
    D.join(blades, f"{name}_blades")
    return {"g": g, "blade": (-100.0, y + 55.0, z), "below": (0.0, y - 80.0, z), "above": (0.0, y + 90.0, z)}


def drift_flow(m, root, beats, name="dfl"):
    x0, y, z = DRB
    for i in range(6):
        xg = -100.0 + 40.0 * i
        # vapour weaves through the gap
        run(root, f"{name}_v{i}", [(xg, y - 90.0, z + 2.0), (xg + 6.0, y - 15.0, z + 2.0), (xg - 2.0, y + 15.0, z + 2.0),
                                   (xg + 6.0, y + 90.0, z + 2.0)], 3, 2.2, m["vapour"], beats, 0.0, 0.8, 40)
        # a droplet hits the blade's bend and falls back
        run(root, f"{name}_d{i}", [(xg + 2.0, y - 90.0, z + 3.0), (xg + 10.0, y - 20.0, z + 3.0), (xg + 10.0, y - 100.0, z + 3.0)], 2,
            3.0, m["c_return"], beats, 0.1 + 0.05 * i, 0.85, 40)


DRP = (0.0, BY + 800.0, -40.0)


def drop_bench(m, root, beats, name="drp"):
    """One big water drop falling; vapour leaves its skin; it turns from amber to blue."""
    x, y, z = DRP
    run(root, f"{name}_w", [(x, y + 120.0, z), (x, y, z)], 1, 22.0, m["c_return"], beats, 0.0, 0.0, 90)
    run(root, f"{name}_c", [(x, y, z), (x, y - 120.0, z)], 1, 20.0, m["c_supply"], beats, 0.5, 0.5, 90)
    for k in range(10):
        a = 2 * math.pi * k / 10
        run(root, f"{name}_v{k}", [(x + 24.0 * math.cos(a), y + 40.0, z + 24.0 * math.sin(a)),
                                   (x + 80.0 * math.cos(a), y + 90.0, z + 80.0 * math.sin(a))], 3, 2.4, m["vapour"], beats, 0.05, 0.6, 30)
    return {"drop": (x + 30.0, y + 30.0, z), "vap": (x + 80.0, y + 95.0, z), "below": (x + 30.0, y - 110.0, z)}
