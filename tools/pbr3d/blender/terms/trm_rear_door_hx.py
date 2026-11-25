"""TRM_REAR_DOOR_HX: a row of air-cooled racks, one with a rear-door heat exchanger cut open.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_rear_door_hx.py

No GPU board base: the subject is a rack door. Units are centimetres. Three racks stand in a row,
fronts at z = 0 (cold aisle), rears at z = -110 (hot aisle). The left rack has no door, so its hot
exhaust spills into the room. The middle rack wears a rear-door heat exchanger, drawn with its outer
grille cut away: copper tubes threaded through aluminium fins, top and bottom headers, hoses down to
an under-floor water loop and a CDU at the row's end. The right rack has a closed door too. Amber =
hot air / warm water, blue = cooled air / cool water.

Beats:
  0 row       racks blow hot air out the back into the room
  1 door      the door coil, cut open
  2 air       hot exhaust goes in, room-temperature air comes out
  3 water     the coil's water carries the heat to a CDU and the facility loop
  4 retrofit  a bridge for older halls; who sells them
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat, tube  # noqa: E402
from power_vrm_detail import frame, run, rise, blink, polyline  # noqa: E402

SLUG = "TRM_REAR_DOOR_HX"
BEATS = [
    ("Air-cooled servers blow their heat out the back of the rack",
     "In a classic data hall, server fans pull cool air in at the front and push hot air out the back into a hot "
     "aisle, and room air handlers have to cool it all again. That works up to about 15 to 25 kW per rack. Denser "
     "AI racks would overwhelm the room's air handlers."),
    ("A rear-door heat exchanger is a water coil hung on the rack's back",
     "The rack's rear door is replaced by a radiator: copper tubes carrying water, threaded through thousands of thin "
     "aluminium fins, fed by headers at top and bottom. Hoses drop to a water loop under the floor or overhead. The "
     "door is about 15 to 25 cm thick and swings open like a normal door for service."),
    ("Hot exhaust goes in, room-temperature air comes out",
     "The servers' own fans push their exhaust straight through the coil, or fans in the door help (an active door). "
     "The water soaks up the heat, so air leaves the rack near room temperature and the room barely notices the "
     "rack is there. One door can remove roughly 30 to 70 kW."),
    ("The water carries the heat to a CDU and out of the building",
     "The coils run on a closed loop kept above the room's dew point so they never sweat. A coolant distribution unit "
     "(CDU) at the end of the row pumps that loop and passes the heat through a plate heat exchanger to the "
     "facility's chilled or warm water, which takes it to chillers or dry coolers."),
    ("A bridge that lets old halls host AI racks",
     "Rear doors need no changes to the servers, so operators use them to retrofit existing air-cooled halls for "
     "40 to 70 kW racks, or alongside direct-to-chip racks to catch the heat the cold plates miss. Makers: Vertiv "
     "(VRT), nVent (NVT), Schneider Electric, Motivair (part of Schneider) and USystems."),
]

RD = 110.0  # rack depth
RH = 210.0
RW = 60.0
RXS = (-100.0, -30.0, 40.0)  # rack x0s (left, door-cut, right)
DZ = (-RD - 22.0, -RD)  # door z range (back face at -132)
CDU = (120.0, 190.0)


def mats(m):
    m["skin"] = mat("rd_skin", (0.78, 0.80, 0.82), metal=0.5, rough=0.4)
    m["rack"] = mat("rd_rack", (0.08, 0.08, 0.10), metal=0.4, rough=0.5)
    m["tray"] = mat("rd_tray", (0.30, 0.31, 0.35), metal=0.6, rough=0.4)
    m["tile"] = mat("rd_tile", (0.55, 0.56, 0.58), rough=0.7)
    m["fin"] = mat("rd_fin", (0.75, 0.77, 0.80), metal=0.85, rough=0.3)
    m["pipe_s"] = mat("rd_pipe_s", (0.20, 0.38, 0.70), metal=0.5, rough=0.35)
    m["pipe_r"] = mat("rd_pipe_r", (0.62, 0.34, 0.20), metal=0.5, rough=0.35)
    m["hose"] = mat("rd_hose", (0.10, 0.10, 0.11), rough=0.8)
    m["a_hot"] = mat("rd_g_hot", (1.0, 0.45, 0.15), emit=(1.0, 0.40, 0.10), strength=4.0)
    m["a_cool"] = mat("rd_g_cool", (0.40, 0.80, 1.0), emit=(0.35, 0.78, 1.0), strength=4.0)
    m["w_warm"] = mat("rd_g_ww", (1.0, 0.62, 0.18), emit=(1.0, 0.55, 0.12), strength=4.0)
    m["led"] = mat("rd_led", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=3.0)
    m["coil_g"] = mat("rd_coil_g", (0.9, 0.5, 0.2), emit=(1.0, 0.5, 0.15), strength=1.5)


def rack(m, root, name, x0, leds):
    g = empty(name, root)
    x1 = x0 + RW
    for px in (x0, x1 - 4.0):
        for pz in (-RD, -4.0):
            bx(f"{name}_p{px:.0f}{pz:.0f}", (px, 0.0, pz), (px + 4.0, RH, pz + 4.0), m["rack"], g)
    bx(f"{name}_top", (x0, RH - 4.0, -RD), (x1, RH, 0.0), m["rack"], g)
    bx(f"{name}_sl", (x0, 0.0, -RD), (x0 + 1.0, RH, 0.0), m["rack"], g)
    bx(f"{name}_sr", (x1 - 1.0, 0.0, -RD), (x1, RH, 0.0), m["rack"], g)
    trays, fans = [], []
    for k in range(18):
        y = 10.0 + k * 10.8
        trays.append(bx(f"{name}_t{k}", (x0 + 4.0, y, -RD + 6.0), (x1 - 4.0, y + 8.6, -2.0), m["tray"], g))
        bx(f"{name}_l{k}", (x0 + 8.0, y + 2.0, -1.8), (x0 + 12.0, y + 3.5, -1.5), m["led"], leds)
        for j in range(4):  # rear fan hubs
            fx = x0 + 10.0 + 13.0 * j
            fans.append(tube(f"{name}_f{k}{j}", (fx, y + 4.3, -RD + 6.0), (fx, y + 4.3, -RD + 5.0), 3.6, m["dark"], g, 12))
    D.join(trays, f"{name}_trays")
    D.join(fans, f"{name}_fans")
    return g


def door(m, root, name, x0, cut=False):
    """Rear-door coil. cut: grille omitted and the fin pack trimmed on the left half to show tubes."""
    g = empty(name, root)
    x1 = x0 + RW
    z0, z1 = DZ
    bx(f"{name}_fl", (x0, 0.0, z0), (x0 + 3.0, RH, z1), m["rack"], g)
    bx(f"{name}_fr", (x1 - 3.0, 0.0, z0), (x1, RH, z1), m["rack"], g)
    for k, mt in ((0, "pipe_s"), (1, "pipe_r")):  # bottom supply header, top return header
        y = 8.0 if k == 0 else RH - 8.0
        tube(f"{name}_hd{k}", (x0 + 3.0, y, (z0 + z1) / 2), (x1 - 3.0, y, (z0 + z1) / 2), 3.2, m[mt], g, 16)
    fins = []
    xa = x0 + (RW / 2 if cut else 3.0)
    for k in range(48):
        y = 14.0 + k * 3.9
        fins.append(bx(f"{name}_fin{k}", (xa, y, z0 + 4.0), (x1 - 3.0, y + 0.6, z1 - 2.0), m["fin"], g))
    D.join(fins, f"{name}_fins")
    tubes = []
    for j in range(5):  # serpentine passes: vertical copper tubes
        x = x0 + 7.0 + (RW - 14.0) * j / 4
        for dz in (-6.0, 6.0):
            tubes.append(tube(f"{name}_tb{j}{dz:.0f}", (x, 8.0, (z0 + z1) / 2 + dz), (x, RH - 8.0, (z0 + z1) / 2 + dz), 1.1, m["copper"], g, 8))
    D.join(tubes, f"{name}_tubes")
    if not cut:
        gr = []
        for k in range(40):
            y = 4.0 + k * 5.1
            gr.append(bx(f"{name}_gr{k}", (x0 + 3.0, y, z0 - 0.6), (x1 - 3.0, y + 2.4, z0), m["rack"], g))
        D.join(gr, f"{name}_grille")
    glow = empty(f"{name}_glow", root)
    for j in range(5):
        x = x0 + 7.0 + (RW - 14.0) * j / 4
        bx(f"{name}_gw{j}", (x - 0.6, 12.0, z0 + 1.6), (x + 0.6, RH - 12.0, z0 + 2.4), m["coil_g"], glow)
    show(glow, [])
    return glow


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    tiles = []
    for i in range(7):
        for j in range(5):
            x, z = -160.0 + 60.0 * i, -240.0 + 60.0 * j
            tiles.append(bx(f"tile{i}{j}", (x + 0.5, -4.0, z + 0.5), (x + 59.5, 0.0, z + 59.5), m["tile"], root))
    D.join(tiles, "floor")
    bx("subfloor", (-160.0, -40.0, -240.0), (260.0, -4.0, 60.0), m["dark"], root)
    leds = empty("leds", root)
    for k, x0 in enumerate(RXS):
        rack(m, root, f"rk{k}", x0, leds)
    gmid = door(m, root, "door1", RXS[1], cut=True)
    door(m, root, "door2", RXS[2])
    # CDU at the row's end
    cx0, cx1 = CDU
    bx("cdu", (cx0, 0.0, -120.0), (cx1, 200.0, -10.0), m["skin"], root)
    bx("cdu_scr", (cx0 + 15.0, 160.0, -9.8), (cx0 + 50.0, 180.0, -9.0), m["screen"], root)
    # water loop under the floor (seen through the cut subfloor front) to both doors
    zc = (DZ[0] + DZ[1]) / 2
    sup = [(cx0 + 20.0, -20.0, -60.0), (cx0 + 20.0, -20.0, zc), (RXS[1] + 10.0, -20.0, zc), (RXS[1] + 10.0, 8.0, zc),
           (RXS[1] + RW - 10.0, 8.0, zc)]
    ret = [(RXS[1] + RW - 6.0, RH - 8.0, zc), (RXS[1] + RW - 6.0, RH + 14.0, zc), (cx0 + 40.0, RH + 14.0, zc),
           (cx0 + 40.0, RH + 14.0, -60.0), (cx0 + 40.0, 200.0, -60.0)]
    polyline("w_sup", sup[:4], 2.4, m["pipe_s"], root)
    polyline("w_ret", ret[:4], 2.4, m["pipe_r"], root)
    polyline("w_ret2", [ret[3], ret[4]], 2.4, m["pipe_r"], root)
    fac = [(cx1 - 15.0, 320.0, -60.0), (cx1 - 15.0, 200.0, -60.0)]
    polyline("fac_in", fac, 4.0, m["pipe_s"], root)
    polyline("fac_out", [(cx1 - 35.0, 200.0, -80.0), (cx1 - 35.0, 320.0, -80.0)], 4.0, m["pipe_r"], root)

    for b in range(5):
        blink(leds, b, [0, 2, 4, 6], n=8, on=0.7)
    # left rack (no door): hot air spills out and rises all beats
    for k in range(6):
        y = 20.0 + 32.0 * k
        run(root, f"hot_l{k}", [(RXS[0] + 30.0, y, -RD + 4.0), (RXS[0] + 30.0, y + 10.0, -RD - 40.0), (RXS[0] + 25.0, y + 40.0, -RD - 80.0)],
            3, 3.6, m["a_hot"], [0, 2, 4], 0.0 + 0.04 * k, 0.6 + 0.04 * k, 45)
    # door rack: hot in, cool out (beats 2-4), coil glows
    show(gmid, [(F(2, 0.1), F(4, 0))])
    for k in range(6):
        y = 20.0 + 32.0 * k
        x = RXS[1] + 20.0 + 4.0 * (k % 3)
        run(root, f"thru{k}", [(x, y, -RD + 4.0), (x, y, DZ[1])], 3, 3.2, m["a_hot"], [2, 3, 4], 0.04 * k, 0.6 + 0.04 * k, 30)
        run(root, f"out{k}", [(x, y, DZ[0]), (x, y + 6.0, DZ[0] - 50.0)], 3, 3.2, m["a_cool"], [2, 3, 4], 0.1 + 0.04 * k, 0.7 + 0.04 * k, 35)
    # water: beat 1 lightly, 3-4 fully
    run(root, "ws", sup, 8, 2.8, m["a_cool"], [1, 3, 4], 0.0, 0.7, 60)
    run(root, "wr", ret, 8, 2.8, m["w_warm"], [1, 3, 4], 0.1, 0.8, 60)
    run(root, "wtube", [(RXS[1] + 7.0, 10.0, zc - 6.0), (RXS[1] + 7.0, RH - 10.0, zc - 6.0)], 6, 1.6, m["w_warm"], [1, 3], 0.0, 0.7, 40)
    run(root, "fi", fac, 5, 3.6, m["a_cool"], [3, 4], 0.0, 0.7, 40)
    run(root, "fo", [(cx1 - 35.0, 200.0, -80.0), (cx1 - 35.0, 320.0, -80.0)], 5, 3.6, m["w_warm"], [3, 4], 0.1, 0.8, 40)

    mid = RXS[1] + RW / 2
    tags = {
        0: [("hot exhaust into the room", (RXS[0] + 30.0, 150.0, -RD - 60.0)), ("server fans at the rear", (RXS[0] + 20.0, 60.0, -RD + 5.0)),
            ("rear-door coils", (RXS[2] + 30.0, RH, DZ[0]))],
        1: [("copper tubes carry water", (RXS[1] + 7.0, 120.0, zc - 6.0)), ("aluminium fin pack", (mid + 15.0, 160.0, DZ[0] + 4.0)),
            ("supply header (bottom)", (mid, 8.0, zc)), ("return header (top)", (mid, RH - 8.0, zc))],
        2: [("hot exhaust in", (RXS[1] + 22.0, 100.0, -RD + 2.0)), ("room-temp air out", (RXS[1] + 22.0, 140.0, DZ[0] - 40.0)),
            ("30-70 kW per door", (mid, RH + 5.0, DZ[0]))],
        3: [("cool water up from floor", (RXS[1] + 10.0, -10.0, zc)), ("warm water back overhead", (cx0, RH + 14.0, zc)),
            ("CDU + facility water", (cx0 + 35.0, 200.0, -60.0))],
        4: [("no server changes needed", (RXS[1] + 30.0, RH, -RD)), ("VRT, NVT, Schneider/Motivair", (cx0 + 35.0, 200.0, -60.0))],
    }
    C.tags(root, tags)
    pi = 3.14159
    C.done(SLUG, BEATS, [
        frame((20.0, 100.0, -150.0), 380.0, pi - 0.45, 0.30),
        frame((mid - 5.0, 110.0, DZ[0]), 240.0, pi - 0.35, 0.20),
        [(0.0, frame((mid - 20.0, 110.0, -150.0), 280.0, pi + 0.7, 0.20)), (0.55, frame((mid - 20.0, 110.0, -150.0), 280.0, pi + 1.1, 0.25))],
        frame((70.0, 100.0, -120.0), 400.0, pi + 0.5, 0.30),
        frame((30.0, 110.0, -100.0), 460.0, pi - 0.6, 0.40, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
