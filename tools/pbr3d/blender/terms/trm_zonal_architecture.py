"""TRM_ZONAL_ARCHITECTURE: a car seen from above with its body off, first wired the old way (dozens
of ECUs, point-to-point harness) then zonal (four zone controllers on an Ethernet backbone to a
central computer).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_zonal_architecture.py

Uses the car kit in trm_adas.py.

Beats:
  0 old       one ECU per feature, each wired to its own sensors and to the others: a copper tangle
  1 zones     the tangle goes; four zone controllers and one central computer appear
  2 data      sensors feed the nearest zone; frames ride the Ethernet backbone to the centre
  3 update    an over-the-air update lands at the centre and fans out to every zone
  4 payoff    harness copper before and after; who sells the chips
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, tube  # noqa: E402
from power_vrm_detail import frame, run, blink  # noqa: E402
import trm_adas as K  # noqa: E402

SLUG = "TRM_ZONAL_ARCHITECTURE"
BEATS = [
    ("The old way: one box per feature, wired point to point",
     "A conventional car has 70 to 150 electronic control units (ECUs), one for the windows, one for the seats, one "
     "for the brakes and so on, each wired to its own sensors and to the others. The harness that ties them together "
     "can run to several kilometres of copper and weigh 50 kg or more, and it is one of the costliest parts to build."),
    ("Zonal: a few zone controllers by location, one central brain",
     "A zonal architecture groups everything by where it sits in the car. A zone controller in each corner powers and "
     "talks to the sensors, lights and motors near it, and a central high-performance computer runs the actual "
     "features as software. Dozens of ECUs collapse into a handful of boxes."),
    ("Sensors talk to the nearest zone; Ethernet carries it to the centre",
     "Each sensor or actuator now needs only a short wire to its zone. The zones join the central computer over a "
     "few automotive Ethernet links (1 to 10 Gbit/s) instead of hundreds of dedicated wires, and the same backbone "
     "can carry camera data for driver assistance."),
    ("Software updates reach the whole car over the air",
     "With the logic in one central computer, a carmaker can ship a new feature or a fix over the cellular link and "
     "push it to every zone, the way phones update. That is the core of the 'software-defined vehicle' carmakers "
     "are moving to."),
    ("Less copper, more central chips",
     "Fewer, shorter wires cut harness weight and assembly cost substantially. The shift moves silicon spend from "
     "many cheap microcontrollers to a few high-performance SoCs, zone MCUs and Ethernet switches. Related: NXP "
     "(NXPI), Infineon (IFNNY), Renesas (6723.T), Marvell (MRVL) for automotive Ethernet."),
]

Y = 34.0  # parts sit on the floor pan


def ecu(m, parent, name, c, w=16.0, d=12.0, mt="dark"):
    x, y, z = c
    bx(f"{name}_b", (x - w / 2, y, z - d / 2), (x + w / 2, y + 7, z + d / 2), m[mt], parent)
    bx(f"{name}_c", (x - w / 2 - 2, y + 2, z - 3), (x - w / 2, y + 6, z + 3), m["plastic"], parent)
    return (x, y + 7, z)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.car_mats(m)
    K.road(m, root, -500.0, 500.0, -260.0, 260.0)
    car = K.car(m, root, "car", cut=False, cabin=False, driver=False)

    # sensors and actuators: lights, mirrors, doors, seats, cameras, radars round the car
    ends = []
    sens = empty("sens", root)
    for x in (-215.0, -140.0, -40.0, 60.0, 150.0, 215.0):
        for z in (-78.0, 78.0):
            ends.append((x, Y, z))
            bx(f"s{x:.0f}_{z:.0f}", (x - 4, Y, z - 4), (x + 4, Y + 5, z + 4), m["mold"], sens)
    for x in (-215.0, 215.0):
        ends.append((x, Y, 0.0))
        bx(f"s{x:.0f}_0", (x - 4, Y, -4), (x + 4, Y + 5, 4), m["mold"], sens)

    # beat 0: the old way. 16 ECUs, each wired to a few sensors and to many other ECUs
    old = empty("old", root)
    ecus = []
    for k in range(16):
        x = -170.0 + (k % 8) * 48.0
        z = -40.0 if k < 8 else 40.0
        ecus.append(ecu(m, old, f"ecu{k}", (x, Y, z + 12 * math.sin(k))))
    wires = []
    for k, e in enumerate(ecus):
        for j in (3, 7, 11):
            s = ends[(k * 5 + j) % len(ends)]
            mid = ((e[0] + s[0]) / 2, Y + 10 + 4 * (k % 3), (e[2] + s[2]) / 2)
            wires.append(D.polyline(f"ow{k}_{j}", [e, mid, s], 0.55, m["copper"], old))
        for j in (1, 5, 9):
            o = ecus[(k + j) % 16]
            wires.append(D.polyline(f"oe{k}_{j}", K.D.arc(e, o, 10 + 3 * (j % 4), 6), 0.5, m["copper"], old))
    D.join(wires, "old_harness")
    D.present(old, [(F(0, 0), F(1, 0.2))])
    old_beads = []
    for k in range(0, 16, 3):
        e, o = ecus[k], ecus[(k + 5) % 16]
        run(root, f"ob{k}", K.D.arc(e, o, 14, 6), 3, 1.4, m["v12"], [0], 0.1, 0.8, 30)

    # beats 1+: zonal
    new = empty("zonal", root)
    zones = [(-100.0, Y, -55.0), (-100.0, Y, 55.0), (95.0, Y, -55.0), (95.0, Y, 55.0)]
    zc = [ecu(m, new, f"zone{k}", c, 26.0, 20.0, "alu") for k, c in enumerate(zones)]
    hpc = ecu(m, new, "hpc", (0.0, Y, 0.0), 44.0, 36.0, "alu")
    fins = [bx(f"hpc_f{k}", (-20 + k * 5, Y + 7, -16), (-18 + k * 5, Y + 13, 16), m["alu"], new) for k in range(9)]
    D.join(fins, "hpc_fins")
    hglow = empty("hpc_glow", root)
    bx("hpc_g", (-8, Y + 13.2, -8), (8, Y + 13.8, 8), m["die_hot"], hglow)
    show(hglow, [(F(1, 0.3), F(4, 1.0))])
    zg = empty("zone_glow", root)
    for k, c in enumerate(zc):
        bx(f"zg{k}", (c[0] - 4, c[1], c[2] - 4), (c[0] + 4, c[1] + 0.6, c[2] + 4), m["sig"], zg)
    backbone = []
    for k, c in enumerate(zc):
        path = [c, (c[0] * 0.5, Y + 6, c[2] * 0.6), hpc]
        backbone.append(path)
        D.polyline(f"eth{k}", path, 1.0, m["e_blue"], new)
    ring = [zc[0], zc[1], zc[3], zc[2], zc[0]]
    D.polyline("eth_ring", ring, 0.6, m["chan"], new)
    shorts = []
    for k, s in enumerate(ends):
        z_ = min(range(4), key=lambda i: math.dist(zones[i], s))
        shorts.append((s, zc[z_]))
        D.polyline(f"sw{k}", [s, (s[0], Y + 4, (s[2] + zc[z_][2]) / 2), zc[z_]], 0.45, m["copper"], new)
    D.present(new, [(F(1, 0.2), F(4, 0)), (F(4, 0.0), F(5, 0))])
    show(zg, [(F(1, 0.3), F(5, 0))])

    # beat 2: data in
    for k, (s, z_) in enumerate(shorts):
        run(root, f"sd{k}", [s, z_], 2, 1.2, m["sig"], [2], 0.0, 0.35, 18)
    for k, path in enumerate(backbone):
        run(root, f"bb{k}", path, 7, 1.9, m["e_blue"], [2], 0.3, 0.9, 30)

    # beat 3: OTA update
    ant = (-60.0, 70.0, 0.0)
    tube("ant", (-60.0, Y, 0.0), ant, 1.6, m["dark"], root, 8)
    tower = (-420.0, 260.0, -220.0)
    tube("tower", (-420.0, 0.0, -220.0), tower, 5.0, m["steel"], root, 10)
    run(root, "ota_in", [tower, ant, (0.0, Y + 14, 0.0)], 6, 2.6, m["rf"], [3], 0.0, 0.3, 30)
    C.rings(m, root, "ota", tower, [3], n=3, r0=6.0, r1=80.0, mt="rf", axis="y")
    for k, path in enumerate(backbone):
        run(root, f"up{k}", list(reversed(path)), 5, 2.0, m["rf"], [3], 0.4, 0.85, 26)
    for k in range(4):
        blink(zg, 3, [5, 6, 7], n=8, on=0.6)

    # beat 4: copper before/after
    spools = empty("spools", root)
    for k, (x, r, h) in enumerate(((-330.0, 60.0, 90.0), (330.0, 28.0, 40.0))):
        tube(f"spool{k}", (x, 0.0, 190.0), (x, h, 190.0), r, m["copper"], spools, 32)
        tube(f"spf{k}a", (x, 0.0, 190.0), (x, 3.0, 190.0), r + 8, m["plastic"], spools, 32)
        tube(f"spf{k}b", (x, h, 190.0), (x, h + 3.0, 190.0), r + 8, m["plastic"], spools, 32)
    D.present(spools, [(F(4, 0.1), F(5, 0))])

    tags = {
        0: [("~100 ECUs, one per feature", ecus[3]), ("point-to-point copper", (0.0, Y + 14, 20.0)),
            ("km of wire, 50+ kg", car["front"])],
        1: [("zone controller per corner", zc[2]), ("central computer", hpc), ("Ethernet ring", zc[1])],
        2: [("short wire to nearest zone", ends[0]), ("1-10 Gbit/s Ethernet", backbone[3][1]),
            ("features run as software", hpc)],
        3: [("over-the-air update", tower), ("fans out to every zone", zc[3]), ("software-defined vehicle", hpc)],
        4: [("old harness copper", (-330.0, 95.0, 190.0)), ("zonal: far less", (330.0, 45.0, 190.0)),
            ("NXPI, IFNNY, Renesas, MRVL", hpc)],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((0.0, 30.0, 0.0), 520.0, 0.25, 0.95),
        frame((0.0, 30.0, 0.0), 500.0, 0.35, 1.05),
        frame((40.0, 30.0, 20.0), 420.0, 0.45, 0.80),
        frame((-150.0, 80.0, -60.0), 720.0, 0.40, 0.55),
        frame((0.0, 40.0, 100.0), 820.0, 0.15, 0.60),
    ], root)


if __name__ == "__main__":
    build()
