"""The GRID node's nine numbered sections (POWER tab), in the picture-and-panel template
(docs/diagram-pages.md). Section N illustrates heading N of tui/src/screens/diagrams_pages/PWR_GRID.txt,
so the menu title, the text panel and the picture agree; heading 10 (Sources) is text only. Three
beats each, one beat is 8 s.

Run from the repo root, one section per run:

    blender -b --factory-startup --python tools/pbr3d/blender/power_grid_sections.py -- <n>

Writes blender/power_grid_section_<n>.blend and assets/power_grid_section_<n>.glb. The parts (lattice
towers, insulator strings, conductors, generator, transformers, gantry, data hall, gas turbine,
queue) come from power_grid_detail.py.

  1 what happens   the plant feeds the grid; lines on towers at 115-345 kV; the substation steps it down
  2 the parts      TRANSMISSION + THREE-PHASE; UTILITY, QUEUE, LOAD; PUE, BEHIND THE METER, GAS TURBINE
  3 in order       1 generator 2 step-up 3 three-phase lines 4 gantry 5 step-down
  4 high voltage   same power two ways; the low-voltage line runs hot; 10x volts = 1/100 the loss
  5 AI's power     58 -> 176 TWh, 325-580 TWh by 2028, one rack ~120 kW
  6 the queue      studied at the gate; ~1,400 GW + 890 GW waiting; 55 months
  7 PUE, on site   site / IT power; ~1.1-1.2; a gas turbine behind the meter, or a nuclear deal
  8 who makes it   producers and utilities; turbine and grid-equipment makers; transmission builders
  9 chokepoints    queues take years; new lines take a decade; large loads raise prices
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, OFF, label, beat, show, empty, rel  # noqa: E402
from sand_zooms import start, scale_keys  # noqa: E402
import power_grid_detail as D  # noqa: E402
from power_grid_detail import frame, camera_path, run, rise, segment, finish, MB  # noqa: E402
import power_grid_overview as ov  # noqa: E402

PAGE = "power_grid"
BEATS = 3
PH_M = ("ph_a", "ph_b", "ph_c")
CAMPUS = ("ground", "lines", "sub", "hall")
NEAR_TOWERS = (D.TOWERS[2], D.TOWERS[3])


def setup(name):
    _, root = start(name, beats=BEATS, page=PAGE)
    return D.materials(), root


def after(b, u):
    return [(F(b, u), F(BEATS, 0))]


def grow(parent, name, lo, hi, m, f0, f1):
    """A bar from lo to hi that grows up from its base between frames f0 and f1."""
    base = ((lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2)
    pv = empty(name, parent, P(*base))
    D.box(f"{name}_bar", rel(base, lo), rel(base, hi), m, pv)
    scale_keys(pv, [(0, (OFF, OFF, OFF)), (f0, (1, 1, OFF)), (f1, (1, 1, 1))], until=f0 + 1)
    return pv


def tags(root, items):
    for b, text, at in items:
        label(text, at, root, beat(b))


def mid(path, f=0.5):
    return path[int(len(path) * f)]


# ---- 1 what happens -----------------------------------------------------------------------------


def sec1(m, root):
    w = D.world(m, root, ("ground", "plant", "gsu", "lines", "sub", "hall"))
    for k in range(3):
        run(root, f"g{k}", D.join_paths(D.gsu_path(w, k), segment(w["lines"][(1, "ABC"[k])], -2000, D.TOWERS[1])),
            6, 7.5, m["power"], 0, 0.03 * k, 0.6, 100)
    for s in (1, -1):
        for k, ph in enumerate("ABC"):
            run(root, f"l{s}{ph}", w["lines"][(s, ph)], 5, 6.0, m["power"], 1, 0.02 * k, 0.6, 110)
            p = D.join_paths(segment(w["lines"][(s, ph)], D.TOWERS[3], D.GX), D.sub_path(w, s, k))
            run(root, f"s{s}{ph}", p, 4, 4.0, m["power"], 2, 0.02 * k, 0.55, 110)
    p, g, s = w["plant"], w["gsu"], w["sub"]
    tags(root, [
        (0, "power plant feeds the grid", p["hall"]), (0, "generator", p["gen"]), (0, "step-up transformer", g["bushing"]),
        (1, "TRANSMISSION: 115-345 kV", mid(w["lines"][(1, "B")], 0.45)), (1, "steel towers", (D.TOWERS[2] + 30, 180.0, 30.0)),
        (2, "lines drop into the substation", (D.GX, 252.0, 118.0)), (2, "it steps the voltage down", s["sd"]["bushing"]),
        (2, "then the campus", (1200.0, D.DH_TOP, -150.0)),
    ])
    camera_path(root, [
        frame((-1180.0, 150.0, -60.0), 680.0, 0.40, 0.30),
        frame((-280.0, 270.0, 20.0), 900.0, 0.50, 0.20),
        frame((960.0, 110.0, -80.0), 860.0, 0.36, 0.36),
    ])


# ---- 2 the parts --------------------------------------------------------------------------------


def sec2(m, root):
    w = D.world(m, root, CAMPUS + ("gt",), NEAR_TOWERS)
    qg = empty("s2_queue", root)
    gs, front = D.queue(m, qg, n=6)
    for k, ph in enumerate("ABC"):
        T0 = NEAR_TOWERS[0]
        run(root, f"t{ph}", segment(w["lines"][(1, ph)], T0 - 300, T0 + 300), 9, 3.5, m[PH_M[k]], 0, 0.04 * k, 0.85, 60)
        run(root, f"tb{ph}", segment(w["lines"][(-1, ph)], T0 - 300, T0 + 300), 6, 3.5, m[PH_M[k]], 0, 0.04 * k, 0.85, 60)
    for s in (1, -1):
        for k in range(3):
            run(root, f"u{s}{k}", D.sub_path(w, s, k), 4, 4.5, m["power"], 1, 0.03 * k, 0.6, 100)
    ring = D.scan_ring(m, root, (front[0], 30.0, front[2]), 52.0)
    show(ring, beat(1))
    for k in range(3):
        run(root, f"it{k}", D.join_paths(w["sub"]["lv"][k], w["hall"]["rows"][k]), 5, 4.0, m["power"], 2, 0.03 * k, 0.6, 80)
    ov.turbine_runs(m, root, w, 2)
    h, gt, s = w["hall"], w["gt"], w["sub"]
    T = NEAR_TOWERS[0]
    tags(root, [
        (0, "TRANSMISSION line", (T, 400.0, 34.0)), (0, "THREE-PHASE: 3 conductors", (T, 300.0, 92.0)),
        (0, "insulator string", (T, 330.0, 70.0)),
        (1, "UTILITY: owns the wires", (D.GX, 252.0, 118.0)), (1, "INTERCONNECTION QUEUE", (front[0] - 200, 60.0, front[2])),
        (1, "DATA CENTER LOAD", h["roof"]), (1, "meter", s["meter"]),
        (2, "PUE: site power / IT power", h["row"]), (2, "BEHIND THE METER", gt["stack"]), (2, "GAS TURBINE", gt["turb"]),
    ])
    camera_path(root, [
        frame((T, 300.0, 40.0), 240.0, 0.62, 0.10),
        frame((760.0, 60.0, 60.0), 760.0, 0.18, 0.40),
        frame((1340.0, 90.0, -80.0), 640.0, 0.30, 0.34),
    ])


# ---- 3 in order ---------------------------------------------------------------------------------


def sec3(m, root):
    w = D.world(m, root, ("ground", "plant", "gsu", "lines", "sub", "hall"))
    for k in range(3):
        run(root, f"bus{k}", D.gsu_path(w, k), 6, 7.5, m[PH_M[k]], 0, 0.04 * k, 0.7, 80)
        for s in (1, -1):
            run(root, f"ln{s}{k}", segment(w["lines"][(s, "ABC"[k])], D.TOWERS[0], D.TOWERS[3]), 7, 5.5, m[PH_M[k]],
                1, 0.04 * k, 0.8, 100)
            p = D.join_paths(segment(w["lines"][(s, "ABC"[k])], D.TOWERS[3], D.GX), D.sub_path(w, s, k))
            run(root, f"sd{s}{k}", p, 4, 3.5, m[PH_M[k]], 2, 0.04 * k, 0.6, 100)
    p, g, s = w["plant"], w["gsu"], w["sub"]
    T = D.TOWERS[1]
    tags(root, [
        (0, "1 generator: ~10-25 kV", p["gen"]), (0, "2 step-up: raised to line voltage", g["bushing"]),
        (0, "copper windings", g["hv_w"]),
        (1, "3 three phases, tower to tower", (T, 350.0, 70.0)), (1, "one colour per phase", mid(w["lines"][(1, "C")], 0.3)),
        (2, "4 the substation gantry", (D.GX, 252.0, 118.0)), (2, "5 stepped down for the site", s["sd"]["bushing"]),
        (2, "out to the campus", s["meter"]),
    ])
    camera_path(root, [
        frame((-1200.0, 120.0, -40.0), 560.0, 0.30, 0.22),
        frame((-460.0, 280.0, 20.0), 560.0, 0.55, 0.16),
        frame((720.0, 130.0, -10.0), 440.0, 0.42, 0.30),
    ])


# ---- 4 why high voltage -------------------------------------------------------------------------

S4_X = (-260.0, 260.0)
S4_Z = (0.0, -420.0)  # the low-voltage line in front, the high-voltage line behind


def sec4(m, root):
    D.ground(m, root)
    paths = {}
    for li, z0 in enumerate(S4_Z):
        cl = [D.tower(m, root, x, f"s4_t{li}{i}", z0)[0] for i, x in enumerate(S4_X)]
        cond = MB()
        for k, ph in enumerate("ABC"):
            a, b = cl[0][(1, ph)], cl[1][(1, ph)]
            pts = D.curve_pts((a[0] - 300, a[1] - 20, a[2]), a, (0, -20, 0), 6)
            pts += D.curve_pts(a, b, (0, -D.SAG, 0), 12)[1:]
            pts += D.curve_pts(b, (b[0] + 300, b[1] - 20, b[2]), (0, -20, 0), 6)[1:]
            D.wire_into(cond, pts, 1.7, 6)
            paths[(li, ph)] = pts
        cond.obj(f"s4_cond{li}", m["conductor"], root, smooth=True)
    hot = empty("s4_hot", root)
    hmb = MB()
    for ph in "ABC":
        D.wire_into(hmb, paths[(0, ph)], 2.3, 8)
    hmb.obj("s4_hot_wires", m["hot"], hot, smooth=True)
    show(hot, after(1, 0.15))
    for b in range(3):
        for k, ph in enumerate("ABC"):
            run(root, f"lo{b}{ph}", paths[(0, ph)], 16, 4.2, m["power"], b, 0.02 * k, 0.7, 90)
            run(root, f"hi{b}{ph}", paths[(1, ph)], 2, 4.2, m["power"], b, 0.1 + 0.05 * k, 0.6, 90)
    for b in (1, 2):
        for k, ph in enumerate("ABC"):
            for j, f in enumerate((0.25, 0.5, 0.75)):
                rise(root, f"heat{b}{ph}{j}", mid(paths[(0, ph)], f), 3, 4.5, m["heat"], b, 0.1 + 0.08 * j, 0.8, 50,
                     h=70, drift=(6, 0))
    bx = 420.0
    grow(root, "s4_loss_lo", (bx, 0.0, 30.0), (bx + 40, 300.0, 70.0), m["price"], F(2, 0.1), F(2, 0.5))
    grow(root, "s4_loss_hi", (bx, 0.0, -400.0), (bx + 40, 3.0, -360.0), m["bar_hi"], F(2, 0.1), F(2, 0.5))
    lo, hi = paths[(0, "A")], paths[(1, "A")]
    tags(root, [
        (0, "low voltage: 10x the current", mid(lo, 0.45)), (0, "high voltage: 1/10 the current", mid(hi, 0.55)),
        (0, "same power on both", (S4_X[1], 400.0, 34.0)),
        (1, "loss goes with current squared", mid(paths[(0, "B")], 0.4)), (1, "the wire heats", mid(paths[(0, "C")], 0.62)),
        (1, "barely warm", mid(hi, 0.4)),
        (2, "loss: 100", (bx + 20, 300.0, 50.0)), (2, "loss: 1", (bx + 20, 4.0, -380.0)),
        (2, "so lines run at hundreds of kV", mid(hi, 0.4)),
    ])
    camera_path(root, [
        frame((0.0, 230.0, -160.0), 760.0, 0.45, 0.18),
        frame((0.0, 250.0, -60.0), 640.0, 0.40, 0.14),
        frame((160.0, 190.0, -160.0), 900.0, 0.55, 0.20),
    ])


# ---- 5 how much power AI needs -------------------------------------------------------------------

TWH = 0.5  # drawn height per TWh


def big_rack(m, root, x0, z0, name="s5_rack"):
    """A rack drawn large and cut open at its front (z0): steel frame, compute trays, power
    shelves top and bottom, a copper busbar down the back. Returns (busbar path, points)."""
    w, h, d = 70.0, 200.0, 60.0
    fr = MB()
    fr.box((x0, 0, z0 - d), (x0 + w, h, z0 - d + 4))
    fr.box((x0, 0, z0 - d), (x0 + 4, h, z0))
    fr.box((x0 + w - 4, 0, z0 - d), (x0 + w, h, z0))
    fr.box((x0, h - 4, z0 - d), (x0 + w, h, z0))
    fr.box((x0, 0, z0 - d), (x0 + w, 6, z0))
    fr.obj(f"{name}_frame", m["rack"], root)
    trays, fronts = MB(), MB()
    for k in range(14):
        y = 36 + k * 9.2
        trays.box((x0 + 5, y, z0 - d + 10), (x0 + w - 5, y + 6.5, z0 - 2))
        fronts.box((x0 + 8, y + 2, z0 - 2), (x0 + 14, y + 4.5, z0 - 1))
    trays.obj(f"{name}_trays", m["tray"], root)
    fronts.obj(f"{name}_leds", m["led"], root)
    sh = MB()
    for y in (8.0, 168.0):
        sh.box((x0 + 5, y, z0 - d + 10), (x0 + w - 5, y + 24, z0 - 2))
    sh.obj(f"{name}_shelves", m["cabinet"], root)
    D.box(f"{name}_busbar", (x0 + w / 2 - 4, 8, z0 - d + 5), (x0 + w / 2 + 4, 194, z0 - d + 10), m["copper"], root)
    path = [(x0 + w / 2, 260.0, z0 - d + 8), (x0 + w / 2, 194.0, z0 - d + 8), (x0 + w / 2, 10.0, z0 - d + 8)]
    D.tube(f"{name}_feed", path[0], path[1], 3.0, m["cable"], root, 8)
    return path, {"shelf": (x0 + w / 2, 192.0, z0), "tray": (x0 + w - 5, 120.0, z0), "bus": (x0 + w / 2, 100.0, z0 - d + 10)}


def sec5(m, root):
    D.ground(m, root)
    D.hall(m, root)
    bars = [("2014", 58, 0, m["bar_old"]), ("2023", 176, 0, m["bar"])]
    x = 980.0
    z0, z1 = 140.0, 190.0
    for i, (yr, twh, b, mt) in enumerate(bars):
        grow(root, f"s5_{yr}", (x + i * 80, 0.0, z0), (x + i * 80 + 50, twh * TWH, z1), mt, F(0, 0.1 + 0.25 * i), F(0, 0.35 + 0.25 * i))
    x28 = x + 160
    grow(root, "s5_2028a", (x28, 0.0, z0), (x28 + 50, 325 * TWH, z1), m["bar_hi"], F(1, 0.1), F(1, 0.4))
    grow(root, "s5_2028b", (x28, 0.0, z0 + 2), (x28 + 50, 580 * TWH, z1 - 2), m["bar_ghost"], F(1, 0.5), F(1, 0.8))
    path, rp = big_rack(m, root, 1500.0, 110.0)
    run(root, "s5_rack_pow", path, 10, 4.0, m["power"], 2, 0.0, 0.8, 50)
    for k in range(3):
        run(root, f"s5_rows{k}", [(D.DH[0] + 26, 102, D.ROWS[k]), (D.DH[1] - 20, 102, D.ROWS[k])], 5, 4.0, m["power"],
            2, 0.05 * k, 0.6, 60)
    tags(root, [
        (0, "2014: 58 TWh", (x + 25, 58 * TWH, 165.0)), (0, "2023: 176 TWh, 4.4% of US", (x + 105, 176 * TWH, 165.0)),
        (0, "US data centers, per year", (1200.0, D.DH_TOP, -150.0)),
        (1, "2028: 325-580 TWh projected", (x28 + 25, 580 * TWH, 165.0)), (1, "6.7% to 12% of US power", (x28 + 25, 325 * TWH, 190.0)),
        (1, "2023: 176 TWh", (x + 105, 176 * TWH, 165.0)),
        (2, "one GB200 NVL72 rack: ~120 kW", rp["shelf"]), (2, "power shelves feed the trays", rp["tray"]),
        (2, "campus: 100s of MW to 1+ GW", (1200.0, D.DH_TOP, -150.0)),
    ])
    camera_path(root, [
        frame((1100.0, 70.0, 140.0), 420.0, 0.20, 0.18),
        frame((1110.0, 140.0, 140.0), 460.0, 0.20, 0.16),
        frame((1460.0, 110.0, 20.0), 420.0, 0.35, 0.22),
    ])


# ---- 6 the interconnection queue ------------------------------------------------------------------


def sec6(m, root):
    w = D.world(m, root, CAMPUS, NEAR_TOWERS)
    qg = empty("s6_queue", root)
    gs, front = D.queue(m, qg)
    ring = D.scan_ring(m, root, (front[0], 30.0, front[2]), 52.0)
    show(ring, [(F(0, 0.05), F(1, 0)), (F(2, 0.0), F(2, 0.6))])
    D.box("s6_board", (720.0, 60.0, 330.0), (875.0, 210.0, 332.0), m["tank_in"], root)
    D.box("s6_board_leg", (795.0, 0.0, 328.0), (801.0, 60.0, 332.0), m["lattice"], root)
    lit = D.months(m, root, 728.0, 192.0, 332.0, size=10.0, gap=3.0, per_row=11)
    for i, g in enumerate(lit):
        show(g, after(2, 0.05 + 0.7 * i / len(lit)))
    # beat 2: when the months run out, the front project rolls through the gate and connects
    D.fly(gs[0], [(0, 0, 0), (0, 0, 0)], 0, 1)
    D.fly(gs[0], [(0, 0, 0), (D.GATE_X - front[0] - 10, 0, 0), (D.GATE_X - front[0] - 10, 0, -150.0)], F(2, 0.78), F(2, 0.95))
    for s in (1, -1):
        for k in range(3):
            run(root, f"c{s}{k}", D.sub_path(w, s, k), 3, 4.0, m["power"], 0, 0.1 * k, 0.5, 100)
    q = lambda i: (D.GATE_X - 88.0 * (i + 1) + 40, 40.0, D.QZ)  # noqa: E731
    tags(root, [
        (0, "every project is studied", (front[0], 82.0, front[2] + 50)), (0, "before it may connect", (D.GATE_X + 44, 60.0, 155.0)),
        (0, "a solar farm, waiting", q(0)),
        (1, "~1,400 GW of generation waiting", q(5)), (1, "+890 GW of storage", q(1)), (1, "end of 2024 (LBNL)", q(8)),
        (2, "55 months, request to operation", (798.0, 210.0, 331.0)), (2, "one tile a month", (735.0, 192.0, 333.0)),
        (2, "then it connects", (D.GATE_X + 44, 60.0, 155.0)),
    ])
    camera_path(root, [
        frame((front[0] - 30, 40.0, front[2] - 20), 300.0, -0.35, 0.35),
        frame((240.0, 50.0, 220.0), 820.0, 0.18, 0.36),
        frame((720.0, 110.0, 280.0), 360.0, 0.12, 0.20),
    ])


# ---- 7 PUE and making power on site ----------------------------------------------------------------


def sec7(m, root):
    w = D.world(m, root, CAMPUS + ("gt",), NEAR_TOWERS)
    h = w["hall"]
    D.cooling_tower(m, root, (2150.0, 0.0, -650.0))
    for b in (0, 1):
        for k in range(3):
            run(root, f"it{b}{k}", D.join_paths(w["sub"]["lv"][k], h["rows"][k]), 6, 4.0, m["power"], b, 0.02 * k, 0.7, 80)
        run(root, f"cool{b}", D.join_paths(w["sub"]["lv"][1], h["riser"]), 3, 4.0, m["heat"], b, 0.1, 0.7, 80)
        for i, f in enumerate(h["fans"][::2]):
            rise(root, f"heat{b}{i}", f, 2, 7.0, m["heat"], b, 0.2 + 0.05 * i, 0.9, 60, h=110, drift=(15, 10))
    bx, bz = 1000.0, 140.0
    grow(root, "s7_it", (bx, 0.0, bz), (bx + 50, 100.0, bz + 50), m["bar"], F(1, 0.1), F(1, 0.35))
    grow(root, "s7_total", (bx + 70, 0.0, bz), (bx + 120, 100.0, bz + 50), m["bar"], F(1, 0.1), F(1, 0.35))
    grow(root, "s7_over", (bx + 70, 100.0, bz), (bx + 120, 120.0, bz + 50), m["heat"], F(1, 0.4), F(1, 0.55))
    ov.turbine_runs(m, root, w, 2)
    ctl = MB()
    pts = [(2150.0, 200.0, -520.0), (1900.0, 120.0, -300.0), (1720.0, 40.0, -120.0)]
    D.wire_into(ctl, D.curve_pts(pts[0], pts[2], (0, 40, 0), 10), 2.0, 6)
    ctl.obj("s7_nuke_line", m["cable"], root, smooth=True)
    run(root, "nuke", D.curve_pts(pts[0], pts[2], (0, 40, 0), 10), 5, 6.0, m["power"], 2, 0.1, 0.6, 60)
    gt = w["gt"]
    tags(root, [
        (0, "PUE = site power / IT power", w["sub"]["meter"]), (0, "IT: the racks", h["row"]), (0, "the rest: cooling + losses", h["units"]),
        (1, "IT: 100 MW", (bx + 25, 100.0, bz + 25)), (1, "site: 120 MW = PUE 1.2", (bx + 95, 120.0, bz + 25)),
        (1, "efficient sites: ~1.1-1.2", h["roof"]),
        (2, "GAS TURBINE, behind the meter", gt["stack"]), (2, "or a deal with a nuclear plant", (2150.0, 360.0, -650.0)),
        (2, "the campus", h["roof"]),
    ])
    camera_path(root, [
        frame((1150.0, 90.0, -100.0), 600.0, 0.30, 0.40),
        frame((1100.0, 80.0, 60.0), 520.0, 0.25, 0.30),
        frame((1750.0, 140.0, -300.0), 1200.0, 0.40, 0.30),
    ])


# ---- 8 who makes it ---------------------------------------------------------------------------------


def sec8(m, root):
    w = D.world(m, root)
    D.cooling_tower(m, root, (-1250.0, 0.0, -800.0))
    D.crane(m, root, -180.0, 420.0, h=440.0, jib=200.0)
    D.tower(m, root, 40.0, "s8_new", 420.0, top=250.0)
    for k in range(3):
        run(root, f"all{k}", D.full_path(w, 1, k), 6, 8.0, m["power"], 0, 0.04 * k, 0.55, 150)
        run(root, f"pl{k}", D.gsu_path(w, k), 5, 4.0, m["power"], 1, 0.04 * k, 0.6, 80)
        for s in (1, -1):
            run(root, f"tl{s}{k}", segment(w["lines"][(s, "ABC"[k])], D.TOWERS[0], D.TOWERS[3]), 4, 4.5, m["power"], 2,
                0.04 * k, 0.6, 100)
    p, g, s = w["plant"], w["gsu"], w["sub"]
    tags(root, [
        (0, "power producers: NEE, VST, CEG", p["stack"]), (0, "nuclear: Constellation (CEG)", (-1250.0, 360.0, -800.0)),
        (0, "utilities: Dominion (D), Southern (SO)", (D.GX, 252.0, 118.0)),
        (1, "turbines: GE Vernova (GEV)", p["turbine"]), (1, "Siemens Energy, Mitsubishi Heavy", p["gen"]),
        (1, "grid equipment: GEV, Siemens Energy", g["bushing"]),
        (2, "lines: utilities + contractors", (D.TOWERS[1], 400.0, 34.0)), (2, "Quanta (PWR)", (-180.0, 440.0, 420.0)),
        (2, "a new tower going up", (40.0, 250.0, 420.0)),
    ])
    camera_path(root, [
        frame((-150.0, 300.0, -250.0), 1800.0, 0.50, 0.34),
        frame((-1200.0, 150.0, -60.0), 640.0, 0.40, 0.28),
        frame((-120.0, 230.0, 200.0), 900.0, 0.40, 0.22),
    ])


# ---- 9 chokepoints and risks -----------------------------------------------------------------------


def sec9(m, root):
    w = D.world(m, root, CAMPUS, NEAR_TOWERS)
    qg = empty("s9_queue", root)
    gs, front = D.queue(m, qg, n=8)
    D.box("s9_board", (720.0, 60.0, 330.0), (875.0, 210.0, 332.0), m["tank_in"], root)
    D.box("s9_board_leg", (795.0, 0.0, 328.0), (801.0, 60.0, 332.0), m["lattice"], root)
    lit = D.months(m, root, 728.0, 192.0, 332.0, size=10.0, gap=3.0, per_row=11)
    for i, g in enumerate(lit):
        show(g, after(0, 0.05 + 0.8 * i / len(lit)))
    # a new line under construction behind the old one
    D.tower(m, root, -470.0, "s9_new", 0.0, top=180.0)
    D.crane(m, root, -620.0, -90.0, h=400.0, jib=180.0)
    D.tower(m, root, -850.0, "s9_new2", 0.0, top=60.0)
    # homes beside the campus, and the price over them
    wall, roof = MB(), MB()
    for i in range(6):
        D.house(wall, roof, 1100.0 + i * 70.0, 380.0)
    wall.obj("s9_houses", m["house"], root)
    roof.obj("s9_roofs", m["shingle"], root)
    grow(root, "s9_price0", (1100.0, 60.0, 450.0), (1130.0, 80.0, 470.0), m["price"], F(2, 0.15), F(2, 0.3))
    grow(root, "s9_price1", (1140.0, 60.0, 450.0), (1170.0, 110.0, 470.0), m["price"], F(2, 0.35), F(2, 0.5))
    grow(root, "s9_price2", (1180.0, 60.0, 450.0), (1210.0, 150.0, 470.0), m["price"], F(2, 0.55), F(2, 0.7))
    for s in (1, -1):
        for k in range(3):
            run(root, f"p{s}{k}", D.sub_path(w, s, k), 5, 4.5, m["power"], 2, 0.03 * k, 0.7, 90)
    tags(root, [
        (0, "interconnection queues: years", (front[0] - 200, 60.0, front[2])), (0, "months tick by", (798.0, 210.0, 331.0)),
        (1, "a new line: ~10 years", (-470.0, 180.0, 0.0)), (1, "permits first, then steel", (-850.0, 60.0, 0.0)),
        (1, "today's line, full", (D.TOWERS[2], 400.0, 34.0)),
        (2, "a large load next door", w["hall"]["roof"]), (2, "prices rise for the homes", (1210.0, 150.0, 460.0)),
        (2, "regulators get drawn in", (1100.0, 52.0, 380.0)),
    ])
    camera_path(root, [
        frame((540.0, 80.0, 280.0), 680.0, 0.15, 0.32),
        frame((-420.0, 180.0, 0.0), 860.0, 0.35, 0.18),
        frame((1180.0, 80.0, 150.0), 720.0, 0.20, 0.36),
    ])


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}


def build(n):
    name = f"section_{n}"
    m, root = setup(name)
    SECTIONS[n](m, root)
    finish(name, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ns = [int(a) for a in argv] or list(SECTIONS)
    for n in ns:
        build(n)
