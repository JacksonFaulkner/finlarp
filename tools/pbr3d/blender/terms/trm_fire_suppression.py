"""TRM_FIRE_SUPPRESSION: a clean-agent fire suppression system in a data hall, cut open.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_fire_suppression.py

No GPU board. Units cm. A hall (front wall cut at z = 0) with two rack rows; an aspirating smoke
detection (VESDA-style) sample pipe along the ceiling with sample holes, ceiling spot detectors,
discharge nozzles on a pipe grid. Left: a cylinder room with a bank of agent cylinders, valve heads,
a manifold and the release panel. A pre-action sprinkler pipe (dry) runs above as backup.

Beats:
  0 sense     smoke from one server is sucked into the sample pipe and back to the detector
  1 alarm     panel trips, strobes flash, dampers shut, countdown
  2 discharge cylinders open, agent runs to the nozzles, cloud fills the room in ~10 s
  3 gear safe racks keep running; clean agent leaves no residue; sprinkler stays dry
  4 market    who sells it
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat, tube  # noqa: E402
from power_vrm_detail import frame, run, rise, blink, polyline  # noqa: E402
import trm_chiller as K  # noqa: E402  (rack builder)

SLUG = "TRM_FIRE_SUPPRESSION"
BEATS = [
    ("Pipes sniff the air for smoke before anyone sees it",
     "Data halls use aspirating smoke detection: a thin pipe along the ceiling with small holes, and a fan that pulls "
     "room air through a laser detector. It can catch the faint smoke of an overheating power supply or cable long "
     "before a spot detector would. Ordinary ceiling detectors back it up and confirm."),
    ("Two detectors agree, then the panel counts down",
     "Release usually needs two independent detectors in the same zone to agree, so one dusty sensor cannot dump "
     "the system. The release panel sounds horns and strobes, shuts HVAC dampers so the agent stays in the room, "
     "and runs a 30 to 60 second countdown that staff can hold with an abort button."),
    ("Cylinders dump a gas that fills the room in seconds",
     "A bank of pressurised cylinders opens into a manifold and pipe network, and nozzles at the ceiling discharge "
     "the agent in about 10 seconds (60 to 120 s for inert gases). Clean chemical agents such as FK-5-1-12 or HFC-227ea "
     "pull heat out of the flame; inert gases like IG-541 drop oxygen to around 12-14%, too low to burn."),
    ("The servers keep running, and nothing gets wet",
     "The agents are electrically non-conductive and leave no residue, so equipment that was not burning comes "
     "through untouched and the hall can recover fast. Water would short live gear, so many sites keep a pre-action "
     "sprinkler pipe dry until both a detector and heat at a sprinkler head call for it."),
    ("Every hall needs one, and AI halls are bigger",
     "Fire protection is a small slice of build cost but goes in every data hall, battery room and switchgear room, "
     "and lithium-ion UPS batteries are raising the bar. Makers: Carrier (CARR, Kidde and Marioff), Johnson Controls "
     "(JCI, Tyco, Ansul), Honeywell (HON), Halma (HLMA.L, smoke detection), Siemens and Xtralis (VESDA)."),
]

# hall x -40..520, z -260..0, ceiling y 300. Cylinder room x -260..-40.
HX0, HX1, HZ0, HY = -40.0, 520.0, -260.0, 300.0
CR0 = -260.0
SY = 285.0  # sample pipe height
NY = 290.0  # agent pipe height


def mats(m):
    K.mats(m)
    m["cyl"] = mat("fs_cyl", (0.70, 0.08, 0.07), metal=0.4, rough=0.35)
    m["pipe"] = mat("fs_pipe", (0.68, 0.12, 0.10), metal=0.5, rough=0.4)
    m["vesda"] = mat("fs_vesda", (0.85, 0.20, 0.15), rough=0.5)
    m["det"] = mat("fs_det", (0.92, 0.92, 0.90), rough=0.5)
    m["smoke"] = mat("fs_smoke", (0.55, 0.55, 0.58), emit=(0.55, 0.55, 0.60), strength=1.6)
    m["agent"] = mat("fs_agent", (0.75, 0.90, 1.0), emit=(0.65, 0.88, 1.0), strength=2.2)
    m["strobe"] = mat("fs_strobe", (1.0, 0.25, 0.15), emit=(1.0, 0.22, 0.12), strength=5.0)
    m["sample"] = mat("fs_sample", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=3.0)


def building(m, root):
    g = empty("bldg", root)
    bx("floor", (CR0, -6.0, HZ0), (HX1, 0.0, 0.0), m["concrete"], g)
    bx("back", (CR0, 0.0, HZ0), (HX1, HY, HZ0 + 8.0), m["wall"], g)
    bx("left", (CR0, 0.0, HZ0), (CR0 + 8.0, HY, 0.0), m["wall"], g)
    bx("part", (HX0 - 8.0, 0.0, HZ0), (HX0, HY, -120.0), m["wall"], g)  # wall between rooms, door gap in front
    bx("part_top", (HX0 - 8.0, 220.0, -120.0), (HX0, HY, 0.0), m["wall"], g)
    bx("ceil", (CR0, HY, HZ0), (HX1, HY + 6.0, HZ0 + 30.0), m["wall"], g)  # only a strip: open above
    leds = empty("leds", root)
    for row, z0 in enumerate((-235.0, -125.0)):
        for k in range(6):
            K.rack(m, g, f"rk{row}{k}", 0.0 + 76.0 * k, z0, w=64.0, dep=100.0, h=210.0, leds=leds)
    return leds


def cylinders(m, root):
    g = empty("cyls", root)
    heads = []
    for k in range(5):
        x, z = CR0 + 40.0 + 36.0 * k, -200.0
        tube(f"cy{k}", (x, 4.0, z), (x, 160.0, z), 15.0, m["cyl"], g, 24)
        tube(f"cyd{k}", (x, 160.0, z), (x, 168.0, z), 11.0, m["cyl"], g, 20)
        tube(f"cyv{k}", (x, 168.0, z), (x, 180.0, z), 4.0, m["gold"], g, 12)
        bx(f"cyg{k}", (x - 3.0, 176.0, z + 3.0), (x + 3.0, 182.0, z + 6.0), m["dark"], g)  # gauge
        polyline(f"cyh{k}", [(x, 180.0, z), (x, 196.0, z)], 2.0, m["steel"], g)
        bx(f"cystrap{k}", (x - 16.0, 110.0, z - 16.0), (x + 16.0, 114.0, z - 14.0), m["frame"], g)
        heads.append((x, 196.0, z))
    polyline("manifold", [(heads[0][0] - 10.0, 196.0, -200.0), (heads[-1][0] + 10.0, 196.0, -200.0)], 4.0, m["pipe"], g)
    bx("rack_cyl", (CR0 + 15.0, 120.0, -222.0), (CR0 + 200.0, 126.0, -218.0), m["frame"], g)
    # release panel + abort station on the partition
    bx("panel", (HX0 - 40.0, 120.0, -110.0), (HX0 - 8.0, 180.0, -100.0), m["det"], g)
    scr = empty("panel_led", root)
    for k in range(4):
        bx(f"pl{k}", (HX0 - 36.0 + 7.0 * k, 165.0, -100.0), (HX0 - 32.0 + 7.0 * k, 169.0, -99.0), m["strobe"], scr)
    bx("abort", (HX0 - 30.0, 130.0, -100.0), (HX0 - 18.0, 142.0, -98.0), m["gold"], g)
    # aspirating detector unit
    bx("asd", (HX0 + 4.0, 200.0, -250.0), (HX0 + 34.0, 230.0, -240.0), m["vesda"], g)
    return g, heads, scr


def pipes(m, root):
    g = empty("pipes", root)
    # aspirating sample pipe: from detector up, along the ceiling over both rows, sample holes
    xs = [40.0 + 76.0 * k for k in range(6)]
    samp = [(HX0 + 19.0, 230.0, -245.0), (HX0 + 19.0, SY, -245.0), (HX0 + 19.0, SY, -175.0), (500.0, SY, -175.0)]
    polyline("samp", samp, 1.4, m["vesda"], g)
    for x in xs:
        tube(f"sh{x:.0f}", (x, SY - 1.6, -175.0), (x, SY - 3.0, -175.0), 0.8, m["dark"], g, 8)
    # spot detectors
    for x in xs[::2]:
        tube(f"det{x:.0f}", (x + 30.0, HY - 4.0, -80.0), (x + 30.0, HY, -80.0), 6.0, m["det"], g, 16)
    # agent pipe: manifold -> up -> through the wall -> ceiling grid -> nozzles
    trunk = [(CR0 + 184.0, 196.0, -200.0), (HX0 - 20.0, 196.0, -200.0), (HX0 - 20.0, NY, -200.0), (HX0 + 40.0, NY, -200.0)]
    polyline("ag_trunk", trunk, 3.4, m["pipe"], g)
    nozzles = []
    for zl in (-200.0, -70.0):
        polyline(f"ag_br{zl:.0f}", [(HX0 + 40.0, NY, -200.0), (HX0 + 40.0, NY, zl), (480.0, NY, zl)], 2.6, m["pipe"], g)
        for x in (60.0, 200.0, 340.0, 470.0):
            tube(f"nz{x:.0f}{zl:.0f}", (x, NY, zl), (x, NY - 12.0, zl), 2.2, m["steel"], g, 12)
            tube(f"nzh{x:.0f}{zl:.0f}", (x, NY - 12.0, zl), (x, NY - 15.0, zl), 4.0, m["gold"], g, 12)
            nozzles.append((x, NY - 15.0, zl))
    # pre-action sprinkler, dry: thin steel pipe with heads
    polyline("spr", [(HX0, 270.0, -20.0), (500.0, 270.0, -20.0)], 1.8, m["steel"], g)
    for x in range(20, 500, 80):
        tube(f"spk{x}", (x, 270.0, -20.0), (x, 262.0, -20.0), 1.2, m["gold"], g, 10)
    # HVAC damper on the back wall
    damp = empty("damper", root)
    for k in range(5):
        bx(f"dmp{k}", (300.0, 240.0 + 8.0 * k, HZ0 + 8.0), (380.0, 244.0 + 8.0 * k, HZ0 + 12.0), m["frame"], damp)
    strobes = empty("strobes", root)
    for x in (100.0, 300.0, 480.0):
        bx(f"stb{x:.0f}", (x, 250.0, HZ0 + 8.0), (x + 10.0, 262.0, HZ0 + 12.0), m["strobe"], strobes)
    show(strobes, [])
    return {"samp": samp, "xs": xs, "trunk": trunk, "nozzles": nozzles, "damp": damp, "strobes": strobes}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    leds = building(m, root)
    _, heads, panel = cylinders(m, root)
    p = pipes(m, root)
    for b in range(5):  # racks keep running throughout
        blink(leds, b, [0, 2, 4, 6], n=8, on=0.7)
    # beat 0: smoke off one server (rack 3, front row) rises; samples run back along the pipe
    src = (3 * 76.0 + 32.0, 150.0, -128.0)
    rise(root, "smoke", src, 14, 4.0, m["smoke"], [0, 1], 0.0, 0.85, 120.0, 70, (10.0, 6.0))
    s = p["samp"]
    back = [(s[3][0] - 260.0, SY, -175.0), s[2], s[1], s[0]]
    run(root, "sample", back, 10, 2.0, m["sample"], [0], 0.2, 0.9, 50)
    # beat 1: panel + strobes blink, damper closes (slides down)
    blink(panel, 1, [0, 2, 4, 6], n=8, on=0.5)
    blink(panel, 2, [0, 1, 2, 3, 4, 5, 6, 7], n=8, on=0.9)
    blink(p["strobes"], 1, [0, 2, 4, 6], n=8, on=0.4)
    blink(p["strobes"], 2, [0, 2, 4, 6], n=8, on=0.4)
    C.key(p["damp"], F(1, 0.0), "location", C.P(0.0, 0.0, 0.0))
    C.key(p["damp"], F(1, 0.5), "location", C.P(0.0, -14.0, 0.0))
    # beat 2: agent through the trunk and branches, cloud falling from each nozzle
    allpaths = []
    for h in heads:
        run(root, f"cy_out{h[0]:.0f}", [(h[0], 150.0, h[2]), (h[0], 196.0, h[2])], 3, 2.6, m["agent"], [2], 0.0, 0.2, 15)
    run(root, "ag_t", p["trunk"], 10, 3.0, m["agent"], [2], 0.05, 0.4, 35)
    for k, nz in enumerate(p["nozzles"]):
        br = [(HX0 + 40.0, NY, -200.0), (HX0 + 40.0, NY, nz[2]), (nz[0], NY, nz[2]), nz]
        run(root, f"ag_b{k}", br, 3, 2.6, m["agent"], [2], 0.25, 0.4, 30)
        for j in range(6):
            a = 2 * math.pi * j / 6
            end = (min(500.0, nz[0] + 45.0 * math.cos(a)), 20.0 + 25.0 * (j % 3), nz[2] + 40.0 * math.sin(a))
            allpaths.append(run(root, f"cl{k}_{j}", [nz, (nz[0] + 30.0 * math.cos(a), NY - 40.0, nz[2] + 20.0 * math.sin(a)), end],
                                3, 4.5, m["agent"], [2, 3], 0.35 if j < 3 else 0.45, 0.6, 60))
    tags = {
        0: [("aspirating sample pipe", (300.0, SY, -175.0)), ("smoke from one server", (src[0], 220.0, -128.0)),
            ("laser detector pulls air", (HX0 + 19.0, 235.0, -245.0))],
        1: [("release panel: 2 detectors agree", (HX0 - 24.0, 185.0, -100.0)), ("abort button holds it", (HX0 - 24.0, 128.0, -100.0)),
            ("strobes + horns", (300.0, 262.0, HZ0 + 12.0)), ("dampers shut", (340.0, 230.0, HZ0 + 12.0))],
        2: [("cylinder bank opens", (CR0 + 110.0, 200.0, -200.0)), ("nozzles: full in ~10 s", (200.0, NY - 15.0, -70.0)),
            ("agent cloud fills the room", (260.0, 120.0, -40.0))],
        3: [("racks keep running", (230.0, 215.0, -128.0)), ("no water, no residue", (100.0, 120.0, -20.0)),
            ("pre-action sprinkler: dry", (420.0, 270.0, -20.0))],
        4: [("Carrier/Kidde, JCI/Tyco", (CR0 + 110.0, 210.0, -200.0)), ("Honeywell, Halma, VESDA", (300.0, SY, -175.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        [(0.0, frame((230.0, 190.0, -120.0), 480.0, 0.25, 0.12)), (0.5, frame((120.0, 230.0, -170.0), 420.0, -0.15, 0.22))],
        frame((80.0, 190.0, -120.0), 460.0, 0.35, 0.18),
        [(0.0, frame((-130.0, 150.0, -180.0), 300.0, 0.30, 0.20)), (0.35, frame((130.0, 150.0, -130.0), 800.0, 0.20, 0.22, pad=1.0))],
        frame((230.0, 150.0, -130.0), 560.0, -0.20, 0.20),
        frame((130.0, 150.0, -130.0), 820.0, 0.25, 0.30, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
