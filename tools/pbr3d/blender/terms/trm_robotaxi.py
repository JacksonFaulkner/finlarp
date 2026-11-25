"""TRM_ROBOTAXI: a driverless ride-hail car cut open on a city street, its roof sensor pod, trunk
computer, remote-assistance link and charging depot.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_robotaxi.py

Uses the car kit in trm_adas.py.

Beats:
  0 street    the robotaxi with an empty driver's seat, a rider waiting at the kerb
  1 pod       roof LiDARs spin, cameras and radars ring the car
  2 compute   the trunk computer: every sensor feeds it, it draws ~1 kW and is liquid cooled
  3 remote    the car asks for help; the request goes via a cell tower to an operations centre
  4 depot     back at the depot: charging, cleaning, the economics, who runs them
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, tube  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402
import trm_adas as K  # noqa: E402

SLUG = "TRM_ROBOTAXI"
BEATS = [
    ("A robotaxi is a ride-hail car with nobody in the driver's seat",
     "A robotaxi is a self-driving car run as a paid taxi service with no safety driver aboard. A rider books it in an "
     "app, it pulls up, and the steering wheel turns by itself. Commercial service runs in a small number of cities, "
     "each one gated by local permits, with Waymo the largest operator in the US."),
    ("A roof pod of LiDARs, cameras and radars sees all round",
     "Driving with no human backup needs more sensing than driver assist: several spinning LiDARs that measure the "
     "distance to millions of points a second, a dozen or more cameras and multiple radars, overlapping so any one can "
     "fail. Sensors were once tens of thousands of dollars per car; LiDAR prices have fallen sharply."),
    ("A data-centre-class computer fills the trunk",
     "All those feeds run to a computer in the trunk with one or more high-end AI chips doing perception, prediction "
     "and planning many times a second. It can draw on the order of a kilowatt and is liquid cooled, with redundant "
     "power and a backup path to bring the car to a safe stop if the main system fails."),
    ("When stuck, the car asks a remote human for advice",
     "For odd cases (a blocked lane, police directing traffic) the car pauses and sends its view over the cellular "
     "network to a remote assistance centre. A person there suggests a path; the car still does the driving. How many "
     "cars one assistant can cover is a big lever on cost."),
    ("The business is utilisation, vehicle cost and depots",
     "The operator owns the car, the software, the remote team and the depots where cars charge, get cleaned and are "
     "serviced. Profit depends on paid miles per car per day against the cost of the vehicle and its sensors. "
     "Related: Alphabet (GOOGL, Waymo), Tesla (TSLA), Uber (UBER) as a booking partner, Pony.ai (PONY)."),
]


def building(m, root, name, x0, x1, z0, z1, h, lit):
    g = empty(name, root)
    bx(f"{name}_b", (x0, 0.0, z0), (x1, h, z1), m["grid"], g)
    bx(f"{name}_cap", (x0 - 3, h, z0 - 3), (x1 + 3, h + 4, z1 + 3), m["dark"], g)
    wins = []
    y = 40.0
    while y < h - 30:
        x = x0 + 12
        while x < x1 - 20:
            wins.append(bx(f"{name}_w{x:.0f}_{y:.0f}", (x, y, z1), (x + 16, y + 20, z1 + 0.6), m["dim_glow" if lit else "screen"], g))
            x += 30
        y += 40
    D.join(wins, f"{name}_wins")
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.car_mats(m)
    K.road(m, root, -700.0, 1300.0, -260.0, 220.0)
    bx("pave", (-700.0, 0.0, -420.0), (1300.0, 4.0, -266.0), m["kerb"], root)
    for k, (x0, w, h) in enumerate(((-650, 220, 420), (-400, 260, 300), (-110, 200, 520), (120, 300, 360))):
        building(m, root, f"bld{k}", x0, x0 + w, -700.0, -440.0, h, True)
    taxi = K.car(m, root, "taxi", paint="paint_w", driver=False)
    rider = K.person(m, root, "rider", (120.0, 4.0, -320.0))
    rider.name = "rider"

    # roof pod: a rack, a big spinning LiDAR on top and smaller ones at the corners
    rx, ry, rz = taxi["roof"]
    pod = empty("pod", root)
    bx("pod_rack", (rx - 60, ry, rz - 50), (rx + 60, ry + 8, min(rz + 50, 0.0)), m["dark"], pod)
    bx("pod_fair", (rx - 50, ry + 8, rz - 40), (rx + 50, ry + 20, min(rz + 40, 0.0)), m["paint_w"], pod)
    cams = []
    for k, (dx, dz) in enumerate(((50, -20), (50, -5), (-50, -20), (0, -40))):
        c = (rx + dx, ry + 14, rz + dz)
        tube(f"pod_cam{k}", c, (c[0] + (3 if dx > 0 else -3 if dx < 0 else 0), c[1], c[2] - (3 if dx == 0 else 0)), 3.0, m["glass"], pod, 12)
        cams.append(c)
    lc = (rx, ry + 20.0, rz)
    tube("lidar_base", lc, (lc[0], lc[1] + 6, lc[2]), 18.0, m["dark"], pod, 24)
    spin_g = empty("lidar_spin", root, K.P(lc[0], lc[1] + 6, lc[2]))
    tube("lidar_head", (0, 0, 0), (0, 22, 0), 15.0, m["mold"], spin_g, 24)
    bx("lidar_win", (13.0, 4.0, -6.0), (15.6, 18.0, 6.0), m["chan"], spin_g)
    tube("lidar_cap", (0, 22, 0), (0, 25, 0), 16.0, m["alu"], spin_g, 24)
    C.spin(spin_g, [1, 2, 3], turns=3.0)
    minis = []
    for k, q in enumerate(((222.0, 62.0, -70.0), (-224.0, 66.0, -70.0), (100.0, 84.0, -94.0))):
        tube(f"mini_l{k}", q, (q[0], q[1] + 12, q[2]), 7.0, m["mold"], root, 16)
        minis.append((q[0], q[1] + 6, q[2]))
    # beat 1: sensing
    C.rings(m, root, "lid", (lc[0], lc[1] + 18, lc[2]), [1], n=3, r0=20.0, r1=280.0, mt="dim_glow", axis="xz")
    for k, q in enumerate(minis):
        C.rings(m, root, f"ml{k}", q, [1], n=2, r0=6.0, r1=140.0, mt="chan", axis="xz")
    rd = taxi["radar"]
    for k, dz in enumerate((-160.0, -60.0, 40.0)):
        run(root, f"rad{k}", [rd, (rd[0] + 420, rd[1] + 10, rd[2] + dz)], 4, 2.2, m["rf"], [1], 0.2, 0.8, 34)
    pts_cloud = empty("cloud", root)
    import math
    for k in range(60):
        a = 2 * math.pi * k / 60
        r = 260 + 90 * math.sin(5 * a)
        bx(f"pc{k}", (lc[0] + r * math.cos(a), 6.0 + (k % 5) * 14, lc[2] + r * math.sin(a) * 0.7),
           (lc[0] + r * math.cos(a) + 3, 9.0 + (k % 5) * 14, lc[2] + r * math.sin(a) * 0.7 + 3), m["sig"], pts_cloud)
    D.join(list(pts_cloud.children), "cloud_m")
    show(pts_cloud, [(F(1, 0.45), F(2, 0))])

    # beat 2: trunk computer, wired to everything, liquid loop to a radiator in the nose
    tx, ty, tz = taxi["trunk"]
    glow, conn = K.soc_box(m, root, "cmp", (tx, ty, tz), w=56.0, d=60.0)
    glow2, _ = K.soc_box(m, root, "cmp2", (tx, ty + 26.0, tz), w=56.0, d=60.0)
    show(glow, [(F(2, 0.15), F(5, 0))])
    show(glow2, [(F(2, 0.25), F(5, 0))])
    feeds = [[lc, (rx - 60, ry - 4, rz), (-150, 80, -20), conn],
             [rd, (190, 26, -14), (-150, 28, -14), conn],
             [minis[0], (200, 30, -60), (-150, 30, -60), conn],
             [minis[1], (-215, 44, -50), conn]]
    for k, pts in enumerate(feeds):
        D.polyline(f"feed{k}", pts, 0.9, m["copper"], root)
        run(root, f"fd{k}", pts, 7, 1.7, m["sig"], [2], 0.0, 0.7, 44)
    loop = [(tx + 28, ty + 10, tz), (-120, 28, -60), (190, 28, -60), (215, 40, -60), (215, 40, -30), (190, 30, -30), (-120, 30, -30), (tx + 28, ty + 14, tz + 10)]
    D.polyline("coolant", loop, 1.6, m["rubber"], root)
    bx("radiator", (206, 26, -80), (214, 56, -20), m["alu"], root)
    run(root, "cold", loop[:4], 6, 2.0, m["cool"], [2], 0.1, 0.8, 50)
    run(root, "warm", loop[4:], 6, 2.0, m["heat"], [2], 0.1, 0.8, 50)
    rise(root, "cmp_heat", (tx, ty + 55, tz), 6, 1.3, m["heat"], [2], 0.2, 0.9, 30.0, 50, (14.0, 10.0))

    # beat 3: cell tower and operations centre
    tw = (600.0, 0.0, -520.0)
    tube("tower", tw, (tw[0], 380.0, tw[2]), 5.0, m["steel"], root, 10)
    for k, dy in enumerate((320.0, 350.0)):
        for s in (-1, 1):
            bx(f"ant{k}{s}", (tw[0] + s * 8 - 3, dy, tw[2] - 4), (tw[0] + s * 8 + 3, dy + 26, tw[2] + 4), m["white"], root)
    ops = building(m, root, "ops", 760.0, 1100.0, -700.0, -460.0, 160.0, False)
    scr = empty("ops_screens", root)
    for k in range(5):
        bx(f"ops_s{k}", (780 + k * 62, 40, -459.4), (830 + k * 62, 80, -459.0), m["e_blue"], scr)
    show(scr, [(F(3, 0.4), F(4, 0))])
    up = [(lc[0], lc[1] + 30, lc[2]), (tw[0], 360.0, tw[2])]
    run(root, "up", up, 6, 2.6, m["rf"], [3], 0.05, 0.4, 30)
    run(root, "to_ops", [(tw[0], 360.0, tw[2]), (900.0, 170.0, -580.0)], 4, 2.4, m["rf"], [3], 0.25, 0.5, 26)
    run(root, "back", [(tw[0], 340.0, tw[2]), (lc[0], lc[1] + 30, lc[2])], 5, 2.4, m["sig"], [3], 0.6, 0.85, 30)
    C.rings(m, root, "twr", (tw[0], 360.0, tw[2]), [3], n=3, r0=6.0, r1=90.0, mt="rf", axis="y")
    cone = empty("cones", root)
    for k in range(3):
        tube(f"cone{k}", (380.0 + 30 * k, 0.0, -60.0), (380.0 + 30 * k, 30.0, -60.0), 7.0, m["warn"], cone, 10)
    show(cone, [(F(3, 0), F(4, 0))])

    # beat 4: depot with chargers and a row of taxis
    dep = empty("depot", root)
    dx0 = -650.0
    bx("dep_floor", (dx0, 0.0, 250.0), (dx0 + 900, 3.0, 650.0), m["kerb"], dep)
    bx("dep_roof", (dx0, 180.0, 250.0), (dx0 + 900, 186.0, 650.0), m["alu"], dep)
    for k in range(4):
        tube(f"dep_col{k}", (dx0 + 20 + k * 280, 0, 640.0), (dx0 + 20 + k * 280, 180, 640.0), 5.0, m["steel"], dep, 10)
    plugs = []
    for k in range(3):
        ox = dx0 + 150 + k * 300
        K.car(m, dep, f"dc{k}", ox=ox, oz=450.0, paint="paint_w", cut=False, cabin=True, driver=False)
        bx(f"chg{k}", (ox - 280 + 30, 0, 560), (ox - 280 + 60, 110, 590), m["dark"], dep)
        bx(f"chgs{k}", (ox - 280 + 33, 80, 590), (ox - 280 + 57, 100, 590.6), m["sig"], dep)
        cable = [(ox - 235, 70, 575), (ox - 220, 40, 560), (ox - 205, 50, 545)]
        D.polyline(f"cab{k}", cable, 1.6, m["rubber"], dep)
        plugs.append(cable)
    D.present(dep, [(F(4, 0), F(5, 0))])
    for k, cable in enumerate(plugs):
        run(root, f"chg_b{k}", cable, 4, 1.8, m["v12"], [4], 0.1, 0.9, 30)

    W = K.W
    tags = {
        0: [("no one at the wheel", taxi["sw"]), ("rider waiting at the kerb", (120.0, 92.0, -320.0)),
            ("roof sensor pod", (rx, ry + 40, rz))],
        1: [("spinning LiDAR: 3D point cloud", (lc[0], lc[1] + 30, lc[2])), ("corner LiDARs", minis[0]),
            ("radar sees through rain", (rd[0] + 300, rd[1] + 8, rd[2] - 40)), ("points on everything nearby", (lc[0] + 260, 70.0, lc[2]))],
        2: [("trunk computer, ~1 kW", (tx, ty + 50, tz)), ("redundant second unit", (tx - 20, ty + 30, tz + 20)),
            ("liquid loop to the nose", (215.0, 56.0, -50.0))],
        3: [("car stuck: cones ahead", (410.0, 30.0, -60.0)), ("view sent over cellular", (tw[0], 380.0, tw[2])),
            ("remote assistant suggests a path", (930.0, 80.0, -460.0))],
        4: [("depot: charge, clean, service", (dx0 + 450, 186.0, 450.0)), ("paid miles per car per day", (dx0 + 150, 135.0, 450.0)),
            ("GOOGL, TSLA, UBER, PONY", (dx0 + 750, 135.0, 450.0))],
    }
    _ = W
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((0.0, 100.0, -200.0), 760.0, 0.35, 0.22),
        frame((0.0, 120.0, -60.0), 820.0, 0.45, 0.55),
        frame((-60.0, 70.0, -30.0), 480.0, 0.10, 0.38),
        frame((450.0, 180.0, -350.0), 1050.0, 0.30, 0.22),
        frame((dx0 + 450.0, 70.0, 450.0), 960.0, 0.25, 0.32),
    ], root)


if __name__ == "__main__":
    build()
