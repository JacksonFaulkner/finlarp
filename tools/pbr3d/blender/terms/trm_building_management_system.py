"""TRM_BUILDING_MANAGEMENT_SYSTEM: a data-center plant wired to a BMS controller and operator screen.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_building_management_system.py

No GPU board: a BMS is building controls. Units are centimetres. A plant floor (front cut at z = 0)
holds two chillers, pumps, an air handler, a rack row and a power meter, each with a sensor node.
Thin control cables run to a field controller cabinet (cut open: DDC modules with LEDs) and on to an
operator workstation whose screen shows a plant graphic with trend bars.

Beats:
  0 plant     the equipment the BMS watches
  1 sensors   readings stream from every node to the controller
  2 screen    the controller logs and shows one view of the site
  3 alarm     a supply temperature drifts; alarm, then a setpoint command goes back out
  4 market    wide view, who sells them
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat, tube  # noqa: E402
from power_vrm_detail import frame, run, blink, polyline, rise  # noqa: E402
import trm_chiller as CH  # noqa: E402

SLUG = "TRM_BUILDING_MANAGEMENT_SYSTEM"
BEATS = [
    ("A BMS watches and runs a building's mechanical and electrical plant",
     "A building management system is the network of sensors, controllers and software that runs chillers, pumps, air "
     "handlers and meters. In a data center it is the nervous system for everything that is not IT: the plant that "
     "keeps the racks cool and powered."),
    ("Thousands of sensors report temperature, flow, pressure and power",
     "Every chiller, pump, valve and air handler carries sensors wired to field controllers (DDC panels) over protocols "
     "like BACnet and Modbus. A large site has tens of thousands of points, each sampled every few seconds and logged "
     "for trends and audits."),
    ("Controllers run the control loops; the screen shows one view of the site",
     "Field controllers run local loops on their own: hold supply water at a setpoint, stage chillers, vary pump speed. "
     "The supervisory layer collects all of it into one plant graphic with trends, schedules and energy reports, often "
     "beside the power monitoring and DCIM tools."),
    ("When a reading drifts, it raises an alarm and can reset setpoints",
     "If chilled-water supply creeps above its band or a pump trips, the BMS alarms, can bring a standby unit online "
     "and pushes new setpoints out to the controllers. Good tuning also saves energy: raising water temperatures and "
     "trimming fan speeds lowers PUE."),
    ("AI sites need more controls, and the same vendors supply them",
     "Liquid cooling adds CDUs, more pumps and tighter loops, so control points per MW rise. BMS vendors: Johnson "
     "Controls (JCI, Metasys), Schneider Electric (SU.PA, EcoStruxure), Siemens (SIE.DE, Desigo), Honeywell (HON). "
     "Software is sticky: once a site is wired to one system it rarely switches."),
]

CTRL = (60.0, 0.0, -110.0)  # controller cabinet base
WS = (200.0, 0.0, -80.0)  # workstation desk


def mats(m):
    CH.mats(m)
    m["sense"] = mat("bms_sense", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=3.5)
    m["cmd"] = mat("bms_cmd", (0.30, 0.65, 1.0), emit=(0.25, 0.62, 1.0), strength=3.5)
    m["cable"] = mat("bms_cable", (0.15, 0.40, 0.30), rough=0.6)
    m["scr"] = mat("bms_scr", (0.05, 0.08, 0.12), emit=(0.10, 0.18, 0.28), strength=1.0)
    m["bar"] = mat("bms_bar", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=2.5)


def chiller(m, root, name, x0, z0):
    g = empty(name, root)
    bx(f"{name}_skid", (x0, 0.0, z0), (x0 + 140.0, 6.0, z0 + 60.0), m["frame"], g)
    tube(f"{name}_ev", (x0 + 10.0, 24.0, z0 + 40.0), (x0 + 130.0, 24.0, z0 + 40.0), 16.0, m["shell"], g, 24)
    tube(f"{name}_cd", (x0 + 10.0, 24.0, z0 + 14.0), (x0 + 130.0, 24.0, z0 + 14.0), 12.0, m["shell"], g, 24)
    tube(f"{name}_cp", (x0 + 30.0, 58.0, z0 + 30.0), (x0 + 90.0, 58.0, z0 + 30.0), 12.0, m["steel"], g, 20)
    tube(f"{name}_mo", (x0 + 90.0, 58.0, z0 + 30.0), (x0 + 125.0, 58.0, z0 + 30.0), 11.0, m["motor"], g, 20)
    bx(f"{name}_pnl", (x0 + 2.0, 6.0, z0 + 56.0), (x0 + 26.0, 70.0, z0 + 60.0), m["skin"], g)
    return (x0 + 14.0, 72.0, z0 + 58.0)


def pump(m, root, name, x, z):
    g = empty(name, root)
    bx(f"{name}_base", (x - 14.0, 0.0, z - 10.0), (x + 14.0, 4.0, z + 10.0), m["frame"], g)
    tube(f"{name}_vol", (x, 4.0, z), (x, 22.0, z), 10.0, m["shell"], g, 20)
    tube(f"{name}_mo", (x, 22.0, z), (x, 46.0, z), 8.0, m["motor"], g, 20)
    return (x, 48.0, z)


def node(m, root, name, at, glow):
    """A sensor/transmitter: a small box with a glowing LED; returns the cable start point."""
    x, y, z = at
    bx(f"{name}_box", (x - 3.0, y, z - 2.0), (x + 3.0, y + 6.0, z + 2.0), m["white"], root)
    bx(f"{name}_led", (x - 1.0, y + 6.0, z - 1.0), (x + 1.0, y + 7.0, z + 1.0), m["sense"], glow)
    return (x, y + 6.0, z)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("floor", (-360.0, -6.0, -260.0), (300.0, 0.0, 20.0), m["concrete"], root)
    bx("wall", (-360.0, 0.0, -260.0), (300.0, 200.0, -252.0), m["wall"], root)
    nodes_g = empty("nodes", root)
    pts = []
    pts.append(chiller(m, root, "ch1", -340.0, -240.0))
    pts.append(chiller(m, root, "ch2", -180.0, -240.0))
    pts.append(pump(m, root, "pu1", -310.0, -100.0))
    pts.append(pump(m, root, "pu2", -260.0, -100.0))
    # supply / return headers
    sup = [(-330.0, 30.0, -180.0), (-330.0, 30.0, -100.0), (-120.0, 30.0, -100.0), (-120.0, 30.0, -40.0), (-40.0, 30.0, -40.0)]
    ret = [(-30.0, 120.0, -60.0), (-150.0, 120.0, -60.0), (-150.0, 120.0, -170.0), (-200.0, 40.0, -170.0)]
    polyline("hdr_s", sup, 4.0, m["pipe_s"], root)
    polyline("hdr_r", ret, 4.0, m["pipe_r"], root)
    # air handler + racks
    bx("ahu", (-60.0, 0.0, -80.0), (-20.0, 150.0, -10.0), m["skin"], root)
    pts.append((-40.0, 150.0, -12.0))
    leds = empty("rleds", root)
    for k in range(3):
        CH.rack(m, root, f"rk{k}", -20.0 + 66.0 * k, -250.0, dep=70.0, leds=leds)
    pts.append((80.0, 214.0, -160.0))
    # power meter on the wall
    bx("meter", (-110.0, 120.0, -252.0), (-80.0, 160.0, -246.0), m["skin"], root)
    bx("meter_face", (-106.0, 132.0, -246.0), (-84.0, 152.0, -245.5), m["scr"], root)
    pts.append((-95.0, 160.0, -249.0))
    sens = [node(m, nodes_g, f"n{k}", p, nodes_g) for k, p in enumerate(pts)]
    show(nodes_g, [(0, F(9, 0))])

    # controller cabinet, front open: rails of DDC modules
    cx, cy, cz = CTRL
    cab = empty("cab", root)
    bx("cab_back", (cx - 30.0, 0.0, cz - 20.0), (cx + 30.0, 160.0, cz - 16.0), m["frame"], cab)
    bx("cab_l", (cx - 30.0, 0.0, cz - 20.0), (cx - 27.0, 160.0, cz + 10.0), m["frame"], cab)
    bx("cab_r", (cx + 27.0, 0.0, cz - 20.0), (cx + 30.0, 160.0, cz + 10.0), m["frame"], cab)
    bx("cab_top", (cx - 30.0, 157.0, cz - 20.0), (cx + 30.0, 160.0, cz + 10.0), m["frame"], cab)
    bx("cab_door", (cx + 30.0, 0.0, cz + 10.0), (cx + 33.0, 160.0, cz + 70.0), m["skin"], cab)
    mod_leds = [empty(f"mled{k}", root) for k in range(3)]
    for r in range(4):
        y = 30.0 + 30.0 * r
        bx(f"cab_rail{r}", (cx - 26.0, y, cz - 16.0), (cx + 26.0, y + 2.0, cz - 12.0), m["steel"], cab)
        for k in range(5):
            x = cx - 24.0 + 10.0 * k
            bx(f"cab_mod{r}{k}", (x, y + 2.0, cz - 16.0), (x + 8.0, y + 22.0, cz - 4.0), m["white"], cab)
            bx(f"cab_ml{r}{k}", (x + 2.0, y + 18.0, cz - 4.0), (x + 4.0, y + 20.0, cz - 3.5), m["sense"], mod_leds[(r + k) % 3])
    for k, g_ in enumerate(mod_leds):
        for b in range(5):
            blink(g_, b, [k, k + 3, k + 6] if k + 6 < 8 else [k, k + 3], n=8, on=0.6)
    for b in range(5):
        blink(leds, b, [0, 2, 4, 6], n=8, on=0.7)

    # workstation: desk, monitor with plant graphic and trend bars
    wx, wy, wz = WS
    bx("desk", (wx - 50.0, 70.0, wz - 30.0), (wx + 50.0, 74.0, wz + 20.0), m["tray"], root)
    for x in (wx - 46.0, wx + 42.0):
        bx(f"desk_leg{x:.0f}", (x, 0.0, wz - 26.0), (x + 4.0, 70.0, wz + 16.0), m["frame"], root)
    bx("mon_stand", (wx - 4.0, 74.0, wz - 20.0), (wx + 4.0, 90.0, wz - 16.0), m["frame"], root)
    bx("mon", (wx - 45.0, 90.0, wz - 22.0), (wx + 45.0, 145.0, wz - 18.0), m["frame"], root)
    bx("mon_scr", (wx - 42.0, 93.0, wz - 18.0), (wx + 42.0, 142.0, wz - 17.6), m["scr"], root)
    scr = empty("scr", root)
    for k in range(4):  # plant icons on the screen
        bx(f"scr_ic{k}", (wx - 38.0 + 12.0 * k, 125.0, wz - 17.5), (wx - 30.0 + 12.0 * k, 135.0, wz - 17.2), m["cmd"], scr)
    for k in range(8):  # trend bars
        h = 6.0 + 10.0 * abs(((k * 37) % 11) / 11.0)
        bx(f"scr_b{k}", (wx + 4.0 + 4.5 * k, 97.0, wz - 17.5), (wx + 7.0 + 4.5 * k, 97.0 + h, wz - 17.2), m["bar"], scr)
    show(scr, [(F(2, 0.1), F(9, 0))])
    alarm = empty("alarm", root)
    bx("scr_alarm", (wx - 42.0, 93.0, wz - 17.4), (wx - 4.0, 118.0, wz - 17.1), m["warn"], alarm)
    blink(alarm, 3, [0, 1, 2, 3], n=8, on=0.5, u0=0.0, u1=0.6)
    bad = empty("bad", root)
    p = pts[0]
    bx("bad_led", (p[0] - 3.0, p[1] + 6.0, p[2] - 3.0), (p[0] + 3.0, p[1] + 10.0, p[2] + 3.0), m["warn"], bad)
    blink(bad, 3, [0, 1, 2, 3], n=8, on=0.5, u0=0.0, u1=0.6)
    rise(root, "drift", (p[0] + 60.0, 50.0, -200.0), 6, 2.0, m["heat"], [3], 0.0, 0.4, 40.0, 30, (30.0, 10.0))

    # cable tray overhead; each sensor drops a cable into it and on to the cabinet
    tray_y = 230.0
    bx("tray", (-340.0, tray_y - 2.0, -134.0), (cx + 4.0, tray_y, -126.0), m["steel"], root)
    paths = []
    for k, s in enumerate(sens):
        pth = [s, (s[0], tray_y, s[2]), (s[0], tray_y, -130.0), (cx, tray_y, -130.0), (cx, 160.0, cz - 5.0)]
        polyline(f"cab_c{k}", [pth[0], pth[1], pth[2]], 0.6, m["cable"], root)
        paths.append(pth)
    polyline("trunk_c", [(cx, tray_y, -130.0), (cx, 160.0, cz - 5.0)], 1.4, m["cable"], root)
    lan = [(cx + 20.0, 150.0, cz), (cx + 20.0, 170.0, cz), (wx, 170.0, cz), (wx, 145.0, wz - 20.0)]
    polyline("lan", lan, 0.8, m["cable"], root)
    for k, pth in enumerate(paths):
        run(root, f"s{k}", pth, 3, 2.4, m["sense"], [1, 2, 4], 0.05 * k, 0.6 + 0.04 * k, 60)
    run(root, "lan_up", lan, 6, 2.4, m["sense"], [2, 4], 0.0, 0.7, 40)
    # beat 3: command back to chiller 2 (standby on) and setpoint reset
    back = list(reversed(lan)) + list(reversed(paths[1]))
    run(root, "cmd", back, 6, 2.8, m["cmd"], [3], 0.45, 0.8, 50)

    tags = {
        0: [("chillers", (pts[0][0] + 60.0, 80.0, -210.0)), ("pumps", (-285.0, 50.0, -100.0)),
            ("air handler", (-40.0, 152.0, -40.0)), ("racks", (46.0, 214.0, -200.0)), ("power meter", (-95.0, 160.0, -246.0))],
        1: [("sensor on every unit", pts[1]), ("BACnet / Modbus cables", (-150.0, tray_y, -130.0)),
            ("DDC field controller", (cx, 160.0, cz))],
        2: [("one plant graphic", (wx - 20.0, 140.0, wz - 17.0)), ("trends + energy reports", (wx + 20.0, 110.0, wz - 17.0)),
            ("local loops in the panel", (cx, 100.0, cz - 4.0))],
        3: [("supply temp drifts: alarm", pts[0]), ("standby chiller on", pts[1]),
            ("new setpoint pushed out", (cx + 60.0, 170.0, cz))],
        4: [("JCI Metasys, Siemens Desigo", (cx, 160.0, cz)), ("Schneider, Honeywell", (wx, 145.0, wz - 20.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-80.0, 90.0, -130.0), 600.0, 0.20, 0.35, pad=1.0),
        frame((-80.0, 150.0, -130.0), 580.0, 0.05, 0.50, pad=1.0),
        frame((130.0, 110.0, -100.0), 240.0, 0.10, 0.15),
        [(0.0, frame((-200.0, 80.0, -180.0), 300.0, 0.25, 0.40)), (0.5, frame((-60.0, 120.0, -150.0), 480.0, 0.15, 0.35))],
        frame((-40.0, 100.0, -120.0), 680.0, -0.25, 0.40, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
