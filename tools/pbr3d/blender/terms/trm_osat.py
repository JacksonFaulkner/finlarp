"""TRM_OSAT: outsourced assembly and test, drawn as the packaging line a finished wafer goes down.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_osat.py

Left to right: a wafer arriving from the foundry on a dicing chuck with a spinning saw blade; a
pick head; a large AI package built up in the middle and cut open at the front (organic substrate
with copper layers and BGA balls, silicon interposer on C4 bumps, a GPU die and four HBM stacks on
micro-bumps, then a lid); a test handler with pass/fail lamps; and an output tray.

Beats:
  0 line      wafer in, packaged chips out
  1 dice      the saw cuts the wafer into dies
  2 stack     dies and HBM placed on an interposer, then onto a substrate (2.5D)
  3 test      lid on; every part tested hot, failures binned out
  4 who       ASE, Amkor, JCET; TSMC CoWoS
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, P, bx, empty, mat, show  # noqa: E402
from sand_overview import fly  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_OSAT"
BEATS = [
    ("OSATs turn finished wafers into packaged, tested chips",
     "A wafer leaving the fab is just a disc of bare dies. Outsourced semiconductor assembly and test (OSAT) firms "
     "cut it up, mount each die in a package that can be soldered to a board, and test every part. ASE and Amkor "
     "are the biggest; JCET and others are large in China. Most chip companies, even IDMs, use them for some volume."),
    ("Dicing: a saw cuts the wafer into individual dies",
     "The wafer is taped to a frame and a diamond saw (or a laser) cuts along the thin streets between dies. Good "
     "dies, already marked by wafer probe testing, are picked off the tape. One 300 mm wafer gives a few dozen "
     "huge AI dies or thousands of small ones."),
    ("Advanced packaging: GPU and HBM side by side on silicon",
     "An AI accelerator is not one die but several: a GPU (or two) plus HBM memory stacks placed on a silicon "
     "interposer through tens of thousands of micro-bumps, then mounted on an organic substrate with solder balls "
     "underneath. This 2.5D build (TSMC calls it CoWoS) gives the terabytes per second the GPU needs."),
    ("Lid on, then every part is tested before it ships",
     "A metal lid goes on to spread heat and protect the dies. Then automatic handlers press each part into a "
     "socket and run it hot and cold through electrical tests; failures are binned out. Big AI packages take "
     "longer to test and one bad HBM stack can scrap thousands of dollars of silicon, so test time and yield matter."),
    ("ASE, Amkor and TSMC share the advanced packaging boom",
     "TSMC builds most CoWoS for Nvidia itself, but packaging capacity has been the bottleneck for AI chips, so it "
     "hands overflow and final test to OSATs, which are adding 2.5D lines. Related: Amkor (AMKR), ASE Technology "
     "(ASX), TSMC (TSM). Cost and value per chip rise with die size and the number of HBM stacks."),
]

BELT_Y = 20.0
WC = (-170.0, -60.0)  # dicing chuck centre x, z
PX0, PX1, PZ0 = -50.0, 50.0, -70.0  # package footprint (front cut at z = 0)
TC = (150.0, -60.0)  # tester centre
TR = (215.0, -60.0)  # tray


def mats(m):
    m["wafer"] = mat("os_wafer", (0.45, 0.47, 0.60), metal=0.8, rough=0.15)
    m["tape"] = mat("os_tape", (0.55, 0.70, 0.85), rough=0.3)
    m["blade"] = mat("os_blade", (0.75, 0.76, 0.78), metal=0.95, rough=0.2)
    m["tool"] = mat("os_tool", (0.80, 0.82, 0.84), metal=0.2, rough=0.5)
    m["kerf"] = mat("os_kerf", (0.40, 0.85, 1.0), emit=(0.35, 0.80, 1.0), strength=2.5)
    m["lid"] = mat("os_lid", (0.72, 0.62, 0.45), metal=0.9, rough=0.3)
    m["pass"] = mat("os_pass", (0.35, 1.0, 0.55), emit=(0.30, 1.0, 0.50), strength=3.0)
    m["fail"] = mat("os_fail", (1.0, 0.25, 0.15), emit=(1.0, 0.20, 0.10), strength=3.0)
    m["bump"] = mat("os_bump", (1.0, 0.70, 0.25), emit=(1.0, 0.62, 0.15), strength=2.0)


def dicer(m, root):
    x, z = WC
    g = empty("dc", root)
    bx("dc_base", (x - 40.0, 0.0, z - 40.0), (x + 40.0, BELT_Y, z + 40.0), m["tool"], g)
    D.tube("dc_ring", (x, BELT_Y, z), (x, BELT_Y + 1.0, z), 34.0, m["alu"], g, 64)
    D.tube("dc_tape", (x, BELT_Y + 1.0, z), (x, BELT_Y + 1.3, z), 31.0, m["tape"], g, 64)
    D.tube("dc_wafer", (x, BELT_Y + 1.3, z), (x, BELT_Y + 2.5, z), 26.0, m["wafer"], g, 64)
    dies = []
    for i in range(-4, 5):
        for j in range(-4, 5):
            cx, cz = x + 5.6 * i, z + 5.6 * j
            if (5.6 * i) ** 2 + (5.6 * j) ** 2 < 23.0 ** 2:
                dies.append(bx(f"dc_d{i}_{j}", (cx - 2.5, BELT_Y + 2.5, cz - 2.5), (cx + 2.5, BELT_Y + 2.8, cz + 2.5), m["die"], g))
    D.join(dies, "dc_dies")
    # spindle + blade over the wafer, spinning
    bx("dc_arm", (x - 4.0, BELT_Y + 18.0, z - 45.0), (x + 4.0, BELT_Y + 24.0, z + 5.0), m["alu"], g)
    bx("dc_spin", (x - 12.0, BELT_Y + 6.0, z - 3.0), (x - 4.0, BELT_Y + 18.0, z + 3.0), m["dark"], g)
    hub = empty("dc_hub", root, P(x, BELT_Y + 9.0, z))
    D.tube("dc_bl", (-4.0, 0.0, 0.0), (-3.4, 0.0, 0.0), 7.0, m["blade"], hub, 32)
    for k in range(6):
        a = 2 * math.pi * k / 6
        bx(f"dc_bt{k}", (-4.2, 6.0 * math.cos(a) - 0.6, 6.0 * math.sin(a) - 0.6), (-3.2, 6.0 * math.cos(a) + 0.6, 6.0 * math.sin(a) + 0.6), m["dark"], hub)
    C.spin(hub, [0, 1], turns=6.0, axis=0)
    # kerf lines appear street by street
    kerfs = []
    for k in range(-4, 5):
        e = empty(f"dc_k{k}", root)
        off = 5.6 * k + 2.8
        half = math.sqrt(max(0.0, 25.0 ** 2 - off ** 2))
        bx(f"dc_kx{k}", (x - half, BELT_Y + 2.8, z + off - 0.25), (x + half, BELT_Y + 3.0, z + off + 0.25), m["kerf"], e)
        bx(f"dc_kz{k}", (x + off - 0.25, BELT_Y + 2.8, z - half), (x + off + 0.25, BELT_Y + 3.0, z + half), m["kerf"], e)
        kerfs.append(e)
    return kerfs, {"wafer": (x + 20.0, BELT_Y + 3.0, z + 20.0), "blade": (x - 4.0, BELT_Y + 16.0, z), "dc": (x, BELT_Y + 24.0, z - 40.0)}


def package(m, root):
    """The big 2.5D package, built up in layers, each a group shown from its build moment."""
    y = BELT_Y
    sub, ip, dies, lid = (empty(n, root) for n in ("pk_sub", "pk_ip", "pk_dies", "pk_lid"))
    bx("pk_stand", (PX0 - 10.0, 0.0, PZ0 - 10.0), (PX1 + 10.0, y, 10.0), m["tool"], root)
    balls = []
    for i in range(13):
        b = D.tube(f"bga{i}", (PX0 + 4.0 + 7.6 * i, y, -3.0), (PX0 + 4.0 + 7.6 * i, y + 3.0, -3.0), 2.4, m["solder"], sub, 12)
        balls.append(b)
    D.join(balls, "pk_bga")
    bx("sub_core", (PX0, y + 3.0, PZ0), (PX1, y + 9.0, 0.0), m["substrate"], sub)
    for k, yy in enumerate((y + 4.2, y + 6.0, y + 7.8)):
        bx(f"sub_cu{k}", (PX0, yy, PZ0), (PX1, yy + 0.5, 0.25), m["copper"], sub)
    ix0, ix1 = PX0 + 10.0, PX1 - 10.0
    c4 = [D.tube(f"c4_{i}", (ix0 + 3.0 + 4.0 * i, y + 9.0, -2.0), (ix0 + 3.0 + 4.0 * i, y + 10.6, -2.0), 1.1, m["solder"], ip, 10) for i in range(20)]
    D.join(c4, "pk_c4")
    bx("ip_si", (ix0, y + 10.6, PZ0 + 10.0), (ix1, y + 13.6, 0.0), m["silicon"], ip)
    tsv = [bx(f"tsv{i}", (ix0 + 4.0 + 6.0 * i - 0.3, y + 10.6, -0.6), (ix0 + 4.0 + 6.0 * i + 0.3, y + 13.6, 0.3), m["copper"], ip) for i in range(13)]
    D.join(tsv, "pk_tsv")
    ub = [bx(f"ub{i}", (ix0 + 2.0 + 1.6 * i - 0.4, y + 13.6, -0.8), (ix0 + 2.0 + 1.6 * i + 0.4, y + 14.4, 0.2), m["solder"], dies) for i in range(48)]
    D.join(ub, "pk_ub")
    bx("gpu", (-14.0, y + 14.4, PZ0 + 14.0), (14.0, y + 20.0, 0.0), m["die"], dies)
    hbms = []
    for s in (-1, 1):
        for j, (z0, z1) in enumerate(((PZ0 + 14.0, -30.0), (-28.0, 0.0))):
            xa, xb = sorted((s * 17.0, s * 29.0))
            bx(f"hbm{s}{j}_base", (xa, y + 14.4, z0), (xb, y + 15.6, z1), m["hbm"], dies)
            for n in range(8):
                yy = y + 15.6 + 0.6 * n
                bx(f"hbm{s}{j}_{n}", (xa, yy + 0.1, z0), (xb, yy + 0.6, z1), m["hbm_dram"], dies)
            hbms.append(((xa + xb) / 2, y + 20.4, (z0 + z1) / 2))
    bx("lid_top", (PX0 + 4.0, y + 22.0, PZ0 + 4.0), (PX1 - 4.0, y + 24.0, -4.0), m["lid"], lid)
    for xx in (PX0 + 4.0, PX1 - 8.0):
        bx(f"lid_wall{xx:.0f}", (xx, y + 9.0, PZ0 + 4.0), (xx + 4.0, y + 22.0, -4.0), m["lid"], lid)
    bx("lid_back", (PX0 + 4.0, y + 9.0, PZ0 + 4.0), (PX1 - 4.0, y + 22.0, PZ0 + 8.0), m["lid"], lid)
    bx("tim", (-14.0, y + 20.0, PZ0 + 14.0), (14.0, y + 22.0, -4.0), m["ink"], lid)
    return {"sub": sub, "ip": ip, "dies": dies, "lid": lid}, {
        "sub": (PX1, y + 6.0, 0.0), "bga": (PX0 + 4.0, y + 1.5, -3.0), "ip": (ix1, y + 12.0, 0.0),
        "gpu": (0.0, y + 20.0, -6.0), "hbm": hbms[1], "ub": (ix0 + 10.0, y + 14.0, 0.0), "lid": (0.0, y + 24.0, -30.0)}


def tester(m, root):
    x, z = TC
    g = empty("ts", root)
    bx("ts_body", (x - 30.0, 0.0, z - 40.0), (x + 30.0, 70.0, z - 10.0), m["tool"], g)
    bx("ts_bed", (x - 30.0, 0.0, z - 10.0), (x + 30.0, BELT_Y, z + 30.0), m["tool"], g)
    bx("ts_socket", (x - 12.0, BELT_Y, z - 2.0), (x + 12.0, BELT_Y + 4.0, z + 22.0), m["dark"], g)
    plunger = empty("ts_plunger", root)
    bx("ts_pl", (x - 10.0, BELT_Y + 20.0, z), (x + 10.0, BELT_Y + 26.0, z + 20.0), m["alu"], plunger)
    D.tube("ts_rod", (x, BELT_Y + 26.0, z + 10.0), (x, 70.0, z + 10.0), 2.0, m["alu"], plunger, 12)
    bx("ts_scr", (x - 22.0, 40.0, z - 10.0), (x + 22.0, 62.0, z - 9.6), m["screen"], g)
    ok, bad = empty("ts_ok", root), empty("ts_bad", root)
    for k in range(5):
        bx(f"ts_okl{k}", (x - 18.0 + 7.0 * k, 50.0, z - 9.5), (x - 13.0 + 7.0 * k, 56.0, z - 9.2), m["pass"], ok)
    bx("ts_badl", (x - 18.0, 43.0, z - 9.5), (x + 18.0, 47.0, z - 9.2), m["fail"], bad)
    # output tray and reject bin
    tx, tz = TR
    bx("tray", (tx - 18.0, 0.0, tz - 25.0), (tx + 18.0, 10.0, tz + 25.0), m["dark"], g)
    chips = []
    for i in range(3):
        for j in range(4):
            cx, cz = tx - 11.0 + 11.0 * i, tz - 18.0 + 12.0 * j
            chips.append(bx(f"tr{i}{j}", (cx - 4.0, 10.0, cz - 4.0), (cx + 4.0, 12.0, cz + 4.0), m["lid"], g))
    D.join(chips, "tray_chips")
    bx("rej", (x - 10.0, 0.0, z + 40.0), (x + 10.0, 12.0, z + 55.0), m["fail"] if False else m["plastic"], g)
    return plunger, ok, bad, {"ts": (x, 70.0, z - 25.0), "sock": (x + 12.0, BELT_Y + 4.0, z + 22.0),
                               "tray": (tx, 12.0, tz), "rej": (x, 12.0, z + 48.0)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("floor", (-240.0, -3.0, -140.0), (250.0, 0.0, 60.0), m["grid"], root)
    # conveyor along the front joining the stations
    bx("belt", (-210.0, BELT_Y - 4.0, 12.0), (240.0, BELT_Y - 1.0, 28.0), m["dark"], root)
    for k in range(30):
        xx = -205.0 + 15.0 * k
        bx(f"belt_l{k}", (xx, 0.0, 16.0), (xx + 2.0, BELT_Y - 4.0, 24.0), m["alu"], root)
    kerfs, dp = dicer(m, root)
    grp, pp = package(m, root)
    plunger, ok, bad, tp = tester(m, root)

    # beat 0: a pass along the line; everything built
    run(root, "line", [(-170.0, BELT_Y + 2.0, 20.0), (0.0, BELT_Y + 2.0, 20.0), (TR[0], BELT_Y + 2.0, 20.0), (TR[0], 14.0, TR[1])],
        8, 1.4, m["v12"], [0, 4], 0.0, 0.7, 70)
    # beat 1: kerf lines appear street by street
    for k, e in enumerate(kerfs):
        show(e, [(F(0, 0), F(1, 0)), (F(1, 0.1 + 0.08 * k), F(5, 0))])
    run(root, "chips_fly", [(WC[0], BELT_Y + 3.0, WC[1]), (WC[0], BELT_Y + 15.0, WC[1]), (-90.0, 45.0, -40.0), (0.0, BELT_Y + 18.0, -30.0)],
        6, 1.3, m["kerf"], 1, 0.4, 0.9, 30)
    # beat 2: the package grows layer by layer
    show(grp["sub"], [(F(0, 0), F(1, 0)), (F(2, 0.0), F(5, 0))])
    show(grp["ip"], [(F(0, 0), F(1, 0)), (F(2, 0.2), F(5, 0))])
    show(grp["dies"], [(F(0, 0), F(1, 0)), (F(2, 0.4), F(5, 0))])
    show(grp["lid"], [(F(0, 0), F(1, 0)), (F(3, 0.05), F(5, 0))])
    run(root, "bw", [(-23.0, BELT_Y + 18.0, -0.5), (-23.0, BELT_Y + 14.6, -0.5), (0.0, BELT_Y + 14.6, -0.5)], 6, 0.7, m["bump"], 2, 0.6, 0.95, 20)
    run(root, "bw2", [(23.0, BELT_Y + 18.0, -0.5), (23.0, BELT_Y + 14.6, -0.5), (0.0, BELT_Y + 14.6, -0.5)], 6, 0.7, m["bump"], 2, 0.6, 0.95, 20)
    rise(root, "gpu_heat", (0.0, BELT_Y + 20.0, -30.0), 5, 0.9, m["heat"], 2, 0.6, 0.9, 20.0, 40, (10.0, 10.0))
    # beat 3: plunger presses parts into the socket; pass lamps, one fail goes to the reject bin
    x, z = TC
    for k in range(4):
        f0 = F(3, 0.1 + 0.2 * k)
        for f, dy in ((f0, 0.0), (f0 + 6, -14.0), (f0 + 20, -14.0), (f0 + 26, 0.0)):
            plunger.location = P(0.0, dy, 0.0)
            plunger.keyframe_insert("location", frame=f)
    blink(ok, 3, [1, 3, 7], n=8, on=0.9)
    blink(bad, 3, [5], n=8, on=0.9)
    show(ok, [(F(0, 0), F(1, 0)), (F(3, 0.12), F(3, 0.55)), (F(3, 0.82), F(5, 0))])
    run(root, "reject", [(x, BELT_Y + 5.0, z + 10.0), (x, 30.0, z + 35.0), (x, 14.0, z + 48.0)], 1, 2.0, m["fail"], 3, 0.68, 0.68, 20)
    run(root, "passed", [(x, BELT_Y + 5.0, z + 10.0), (TR[0] - 10.0, 30.0, TR[1]), (TR[0], 14.0, TR[1])], 3, 1.6, m["pass"], 3, 0.3, 0.95, 25)
    rise(root, "hot_test", (x, BELT_Y + 5.0, z + 10.0), 5, 0.9, m["heat"], 3, 0.1, 0.8, 18.0, 40, (8.0, 6.0))

    C.tags(root, {
        0: [("wafer from the foundry", dp["wafer"]), ("2.5D package, cut open", pp["lid"]),
            ("test handler", tp["ts"]), ("packaged chips out", tp["tray"])],
        1: [("diamond saw blade", dp["blade"]), ("cut along the streets", dp["wafer"]), ("good dies picked", (-90.0, 45.0, -40.0))],
        2: [("GPU die", pp["gpu"]), ("HBM stacks", pp["hbm"]), ("silicon interposer + TSVs", pp["ip"]),
            ("substrate + BGA balls", pp["bga"])],
        3: [("lid spreads the heat", pp["lid"]), ("socket test, hot and cold", tp["sock"]), ("fails binned out", tp["rej"])],
        4: [("ASX, AMKR: biggest OSATs", tp["ts"]), ("TSM: CoWoS in-house", pp["lid"]), ("more HBM = more value", pp["hbm"])],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 30.0, -50.0), 460.0, 0.15, 0.45, pad=1.0),
        frame((WC[0], BELT_Y, WC[1]), 90.0, 0.35, 0.65),
        frame((0.0, BELT_Y + 12.0, -25.0), 110.0, 0.30, 0.30),
        frame((90.0, 30.0, -40.0), 260.0, 0.25, 0.35),
        frame((20.0, 30.0, -50.0), 420.0, -0.20, 0.45, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
