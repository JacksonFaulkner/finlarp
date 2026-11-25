"""TRM_OPERATIONAL_TECHNOLOGY: the control systems that run physical equipment, and the IT link.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_operational_technology.py

A plant floor cut open: pumps, a valve train and a chiller loop on the left, a PLC cabinet with
I/O modules in the middle wired to sensors and actuators, an HMI/SCADA desk, then a firewall wall
and an IT room with servers on the right. A cable crosses the boundary; an attacker's packets try
to follow it.

Beats:
  0 floor     OT vs IT: equipment and controllers on one side, servers on the other
  1 loop      sensor -> PLC -> actuator: the control loop runs every few ms
  2 scada     SCADA/HMI watches many PLCs; old protocols, decades-long service lives
  3 converge  IT and OT linked for data and remote ops: beads cross the boundary
  4 attack    red packets probe the link; the firewall blocks; tickers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_OPERATIONAL_TECHNOLOGY"
BEATS = [
    ("OT is the gear that runs physical machines; IT runs the business",
     "Operational technology means the controllers, sensors, drives and screens that switch breakers, run pumps, open "
     "valves and move robot arms. IT means the email, databases and standard servers. Data centers, fabs, factories "
     "and grids all have both, traditionally on separate networks run by separate teams."),
    ("A PLC reads sensors and drives actuators in a tight loop",
     "A programmable logic controller (PLC) reads a pressure or temperature sensor, runs its logic and sets a pump "
     "speed or valve position, over and over every few milliseconds. It must never pause: a missed cycle can mean a "
     "tripped chiller or a burst pipe, so OT values uptime and timing above everything else."),
    ("SCADA screens watch many PLCs over decades-old protocols",
     "Operators watch the plant on HMI and SCADA screens that poll many controllers. Much of it speaks protocols like "
     "Modbus or older fieldbuses that were designed with no passwords or encryption, and the equipment stays in "
     "service for 15-30 years, so patching is rare."),
    ("Plants now link OT to IT for data and remote control",
     "To optimise energy, predict failures and run sites remotely, operators pipe OT data up to IT systems and the "
     "cloud. A data center's power and cooling controls are OT too, and AI halls lean on them heavily. Every new link "
     "is a path that did not exist when the gear was designed."),
    ("Each link widens the attack surface, so the boundary is guarded",
     "An attacker who gets into the office network can try to reach the controllers and stop pumps or open breakers. "
     "Plants answer with segmented zones, firewalls and OT-specific monitoring. Related: Rockwell Automation (ROK), "
     "Emerson (EMR), Honeywell (HON) and Siemens (SIE.DE) sell the controllers and the security around them."),
]

WALL_X = 90.0  # firewall wall between plant (x < WALL_X) and IT room


def mats(m):
    m["floor"] = mat("ot_floor", (0.45, 0.47, 0.48), rough=0.85)
    m["wall"] = mat("ot_wall", (0.70, 0.70, 0.68), rough=0.8)
    m["pump"] = mat("ot_pump", (0.15, 0.35, 0.65), metal=0.5, rough=0.4)
    m["pipe"] = mat("ot_pipe", (0.55, 0.57, 0.60), metal=0.8, rough=0.35)
    m["valve"] = mat("ot_valve", (0.80, 0.20, 0.15), metal=0.4, rough=0.45)
    m["cab"] = mat("ot_cab", (0.82, 0.82, 0.80), metal=0.3, rough=0.5)
    m["io"] = mat("ot_io", (0.20, 0.45, 0.30), rough=0.5)
    m["rack"] = mat("ot_rack", (0.08, 0.08, 0.10), metal=0.5, rough=0.45)
    m["screen"] = mat("ot_screen", (0.30, 0.65, 1.0), emit=(0.30, 0.65, 1.0), strength=2.0)
    m["fw"] = mat("ot_fw", (1.0, 0.62, 0.18), emit=(1.0, 0.55, 0.12), strength=2.5)
    m["led_g"] = mat("ot_led", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=3.0)
    m["sens"] = mat("ot_sens", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=4.0)
    m["cmd"] = mat("ot_cmd", (0.30, 0.65, 1.0), emit=(0.30, 0.65, 1.0), strength=4.0)
    m["data"] = mat("ot_data", (0.85, 0.45, 1.0), emit=(0.80, 0.40, 1.0), strength=4.0)
    m["bad"] = mat("ot_bad", (1.0, 0.25, 0.15), emit=(1.0, 0.25, 0.15), strength=4.0)
    m["water"] = mat("ot_water", (0.30, 0.70, 1.0), emit=(0.25, 0.65, 1.0), strength=3.0)


def pump(m, g, name, x, z):
    p = [bx(f"{name}_base", (x - 10, 0.0, z - 6), (x + 10, 2.0, z + 6), m["steel"], g),
         D.tube(f"{name}_mot", (x - 9, 7.0, z), (x + 1, 7.0, z), 4.5, m["pump"], g, 16),
         D.tube(f"{name}_vol", (x + 2, 7.0, z), (x + 8, 7.0, z), 6.0, m["pump"], g, 16)]
    for k in range(6):
        p.append(bx(f"{name}_fin{k}", (x - 8 + k * 1.5, 2.0, z - 5.2), (x - 7.5 + k * 1.5, 12.0, z + 5.2), m["pump"], g))
    return p


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    g = empty("plant", root)
    s = [bx("floor", (-180.0, -1.5, -130.0), (200.0, 0.0, 0.0), m["floor"], g),
         bx("wall_b", (-180.0, 0.0, -130.0), (200.0, 45.0, -127.0), m["wall"], g),
         bx("wall_l", (-180.0, 0.0, -130.0), (-177.0, 45.0, 0.0), m["wall"], g),
         bx("wall_fw", (WALL_X, 0.0, -127.0), (WALL_X + 3.0, 45.0, -8.0), m["wall"], g)]
    # pumps feeding a header, valve train, tank
    for k in range(3):
        s += pump(m, g, f"pu{k}", -150.0, -100.0 + k * 30.0)
    s.append(bx("hdr", (-138.0, 5.5, -105.0), (-134.0, 9.5, -35.0), m["pipe"], g))
    s.append(bx("main", (-134.0, 5.5, -72.0), (-40.0, 9.5, -68.0), m["pipe"], g))
    s.append(D.tube("tank", (-40.0, 0.0, -70.0), (-40.0, 38.0, -70.0), 14.0, m["steel"], g, 24))
    for k, x in enumerate((-110.0, -85.0, -60.0)):
        s.append(bx(f"vb{k}", (x - 3, 3.5, -74.0), (x + 3, 11.5, -66.0), m["valve"], g))
        s.append(D.tube(f"vs{k}", (x, 11.5, -70.0), (x, 18.0, -70.0), 0.6, m["steel"], g, 8))
        s.append(D.tube(f"vw{k}", (x - 4, 18.0, -70.0), (x + 4, 18.0, -70.0), 0.6, m["valve"], g, 8))
    # sensors on the main: small boxes with glowing heads
    sens_pts = []
    for k, x in enumerate((-120.0, -97.0, -72.0)):
        s.append(bx(f"sn{k}", (x - 1.5, 9.5, -70.5), (x + 1.5, 14.0, -67.5), m["dark"], g))
        sens_pts.append((x, 14.0, -69.0))
    # a robot arm at the front-left (base, links)
    s.append(D.tube("arm0", (-120.0, 0.0, -25.0), (-120.0, 6.0, -25.0), 6.0, m["crane"] if "crane" in m else m["valve"], g, 16))
    arm = empty("arm", root)
    from sand_overview import P
    arm.location = P(-120.0, 6.0, -25.0)
    a = [D.tube("arm1", (0, 0, 0), (0, 22, 0), 2.2, m["valve"], arm, 12),
         D.tube("arm2", (0, 22, 0), (16, 30, 0), 1.8, m["valve"], arm, 12),
         bx("armg", (15, 26, -2), (19, 30, 2), m["dark"], arm)]
    D.join(a, "arm_m")
    C.spin(arm, [1, 2, 3], turns=0.5)
    # PLC cabinet: frame, DIN rails, I/O modules with LEDs, terminal blocks
    cx0, cx1 = 10.0, 40.0
    s.append(bx("cab", (cx0, 0.0, -60.0), (cx1, 40.0, -50.0), m["cab"], g))
    s.append(bx("cab_bp", (cx0 + 1, 2.0, -50.0), (cx1 - 1, 38.0, -49.6), m["white"], g))
    leds = empty("plc_leds", root)
    for r in range(3):
        y = 30.0 - r * 10.0
        s.append(bx(f"din{r}", (cx0 + 2, y, -49.6), (cx1 - 2, y + 1.0, -49.0), m["steel"], g))
        for i in range(8):
            x = cx0 + 3 + i * 3.1
            s.append(bx(f"io{r}{i}", (x, y - 3.0, -49.5), (x + 2.6, y + 6.0, -46.0), m["io"] if r else m["dark"], g))
            bx(f"iol{r}{i}", (x + 0.6, y + 4.0, -45.9), (x + 2.0, y + 5.0, -45.6), m["led_g"], leds)
    D.join(list(leds.children), "plc_ledm")
    show(leds, [(F(1, 0.0), F(5, 0))])
    # HMI / SCADA desk
    s.append(bx("desk", (45.0, 0.0, -30.0), (80.0, 10.0, -18.0), m["dark"], g))
    hmi = empty("hmi", root)
    for k in range(3):
        x = 47.0 + k * 11.0
        s.append(bx(f"mon{k}", (x, 10.0, -28.0), (x + 10.0, 18.0, -27.0), m["dark"], g))
        bx(f"scr{k}", (x + 0.5, 10.5, -27.0), (x + 9.5, 17.5, -26.7), m["screen"], hmi)
    show(hmi, [(F(2, 0.0), F(5, 0))])
    # IT room: server racks
    itl = empty("it_leds", root)
    for i in range(5):
        x = WALL_X + 15 + i * 16
        for zc in (-100.0, -60.0):
            s.append(bx(f"srv{i}{zc:.0f}", (x, 0.0, zc - 10), (x + 10, 32.0, zc + 10), m["rack"], g))
            for j in range(5):
                bx(f"sl{i}{zc:.0f}{j}", (x + 1, 4 + j * 5.5, zc + 10), (x + 9, 4.8 + j * 5.5, zc + 10.3), m["led_g"], itl)
    D.join(list(itl.children), "it_ledm")
    # the cable crossing the boundary, and the firewall appliance in the wall
    s.append(bx("tray", (40.0, 38.0, -57.0), (WALL_X + 100.0, 39.0, -53.0), m["tray"] if "tray" in m else m["steel"], g))
    D.join(s, "plant_m")
    fw = empty("fw", root)
    bx("fwbox", (WALL_X - 3.0, 30.0, -62.0), (WALL_X + 6.0, 42.0, -48.0), m["dark"], fw)
    fwglow = empty("fwglow", root)
    bx("fwshield", (WALL_X - 0.5, 0.5, -126.0), (WALL_X + 3.5, 44.0, -9.0), m["fw"], fwglow)
    show(fwglow, [(F(4, 0.15), F(4, 0.9))])
    fwl = empty("fwl", root)
    bx("fwled", (WALL_X - 3.2, 38.0, -58.0), (WALL_X - 2.9, 40.0, -52.0), m["warn"], fwl)
    blink(fwl, 4, list(range(8)), n=8, on=0.5)

    # beat 1: sensor -> PLC -> valve loop
    for k, sp in enumerate(sens_pts):
        run(root, f"sense{k}", [sp, (sp[0], 30.0, -60.0), (cx0, 30.0, -55.0)], 4, 1.0, m["sens"], [1, 2, 3], 0.0, 0.8, 40)
        vx = (-110.0, -85.0, -60.0)[k]
        run(root, f"cmd{k}", [(cx0, 20.0, -55.0), (vx, 26.0, -62.0), (vx, 18.0, -70.0)], 4, 1.0, m["cmd"], [1, 2, 3], 0.15, 0.95, 40)
    run(root, "flow", [(-134.0, 7.5, -70.0), (-40.0, 7.5, -70.0)], 10, 1.4, m["water"], [1, 2, 3, 4], 0.0, 0.9, 40)
    # beat 2: SCADA polls the PLC
    run(root, "poll", [(60.0, 18.0, -27.0), (40.0, 30.0, -40.0), (cx1, 30.0, -50.0)], 5, 1.0, m["cmd"], [2], 0.0, 0.8, 30)
    run(root, "poll_r", [(cx1, 25.0, -50.0), (40.0, 22.0, -40.0), (60.0, 15.0, -27.0)], 5, 1.0, m["sens"], [2], 0.1, 0.9, 30)
    # beat 3: data crosses to IT along the tray
    run(root, "up", [(cx1, 40.0, -55.0), (WALL_X + 95.0, 40.0, -55.0)], 10, 1.2, m["data"], [3, 4], 0.0, 0.9, 60)
    # beat 4: attacker packets from IT side stop at the wall
    run(root, "atk", [(WALL_X + 95.0, 41.5, -55.0), (WALL_X + 7.0, 41.5, -55.0)], 8, 1.4, m["bad"], [4], 0.0, 0.85, 45)
    rise(root, "pheat", (-150.0, 12.0, -70.0), 6, 0.9, m["heat"], [1], 0.1, 0.9, 14.0, 40, (4.0, 30.0))

    tags = {
        0: [("OT: pumps, valves, robots", (-110.0, 20.0, -70.0)), ("PLC cabinet", (25.0, 41.0, -55.0)),
            ("IT: servers, business apps", (WALL_X + 50.0, 33.0, -80.0)), ("the boundary", (WALL_X, 45.0, -20.0))],
        1: [("sensor reads", sens_pts[0]), ("PLC logic, every few ms", (25.0, 41.0, -55.0)),
            ("valve / pump set", (-85.0, 19.0, -70.0))],
        2: [("SCADA / HMI screens", (60.0, 19.0, -27.0)), ("Modbus: no auth", (40.0, 30.0, -45.0)),
            ("gear lives 15-30 years", (-150.0, 13.0, -70.0))],
        3: [("OT data up to IT / cloud", (WALL_X + 40.0, 40.0, -55.0)), ("new path into the plant", (WALL_X, 42.0, -55.0))],
        4: [("attack from the office side", (WALL_X + 70.0, 42.0, -55.0)), ("firewall + segmented zones", (WALL_X, 30.0, -20.0)),
            ("ROK EMR HON SIE.DE", (25.0, 41.0, -55.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((10.0, 15.0, -65.0), 380.0, 0.25, 0.50, pad=1.0),
        frame((-50.0, 15.0, -60.0), 200.0, 0.20, 0.40),
        frame((20.0, 18.0, -40.0), 150.0, 0.30, 0.35),
        frame((80.0, 25.0, -60.0), 230.0, 0.15, 0.45),
        [(0.0, frame((130.0, 30.0, -55.0), 150.0, -0.30, 0.35)), (0.55, frame((60.0, 20.0, -60.0), 280.0, 0.20, 0.45))],
    ], root)


if __name__ == "__main__":
    build()
