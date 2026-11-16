"""The SUBSTATION node's nine numbered sections, in the picture-and-panel template (docs/diagram-pages.md).
Section N illustrates heading N of tui/src/screens/diagrams_pages/PWR_SUB.txt, so the menu title, the text
panel and the picture agree. Three beats each, one beat is 8 s. (Heading 10, Sources, is text only.)

Run from the repo root, one section per run:

    blender -b --factory-startup --python tools/pbr3d/blender/power_substation_sections.py -- <n>

Writes blender/power_substation_section_<n>.blend and assets/power_substation_section_<n>.glb. The parts
(transformer cut open, yard, teaching core, week rows, steel, ship) come from power_substation_detail.py.

  1 what happens   the line lands on the gantry; the core's field links the windings; 34.5 kV leaves for the campus
  2 the parts      the unit whole; cut open (core, windings, oil, tap changer); an HV bushing in section
  3 in order       1-2 into the bushing and HV winding, 3 the core's flux, 4-5 LV out and oil to the radiators
  4 turns ratio    a teaching core: 20 turns and 2 turns on one field; one turn each lit; 10x volts, 10x amps
  5 losses         the core glows, then the windings; oil carries the heat to the radiators and fans
  6 lead time      rows of weeks: ~50 (2021), ~120 (2024), ~128 and ~144 (Q2 2025)
  7 steel          grain-oriented strip off a coil; sheets stacked into a core; one US mill feeding the line
  8 who makes it   a row of units tagged with their makers; a heavy-lift ship bringing one in
  9 chokepoints    a two-to-three-year row; three custom units and an empty spare plinth; a tariff gate at the dock
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, box, tube, label, beat, show, key, fly  # noqa: E402
from sand_zooms import start  # noqa: E402
from pbr_kit import empty  # noqa: E402
import power_substation_detail as D  # noqa: E402
from power_substation_detail import (frame, camera_path, finish, run, wire, ZC, LXS, HVB_X, LVB_X, HV_TOP,  # noqa: E402
                                     LV_TOP, HVB_Z, LVB_Z, RAD_R, RAD_L, RAD_Y)

BEATS = 3
END = F(BEATS, 0)
B = LXS[1]

CUT_VIEW = frame((30.0, 340.0, ZC), 1050.0, 0.22, 0.12)
CORE_VIEW = frame((0.0, 300.0, ZC), 820.0, 0.12, 0.08)
WHOLE_VIEW = frame((20.0, 520.0, -170.0), 1400.0, 0.38, 0.22)
WIDE_CUT = frame((60.0, 420.0, -170.0), 1500.0, 0.30, 0.16)


def setup(n):
    m, root = start(f"section_{n}", beats=BEATS, page=D.PAGE)
    D.materials(m)
    return m, root


def ground(m, root, x0=-1400.0, x1=1400.0, z0=-900.0, z1=900.0):
    box("ground", (x0, -14.0, z0), (x1, 0.0, z1), m["gravel"], root)


def cut_always(t):
    D.tank_mode(t, [], [(0, END)])
    show(t["front"], [])


def whole_always(t):
    D.tank_mode(t, [(0, END)], [])
    show(t["front"], [(0, END)])


def flux(root, m, t, b, u0=0.0, u1=1.0, name="fx"):
    mid = u0 + (u1 - u0) / 2
    for k in range(2):
        run(root, f"{name}_a{k}", t["flux"][k], 7, 7.0, m["flux"], b, u0, u0 + (mid - u0) * 0.6, 50, 24)
        run(root, f"{name}_b{k}", t["flux_rev"][k], 7, 7.0, m["flux"], b, mid + 0.02, mid + (u1 - mid) * 0.6, 50, 24)


def oil(root, m, t, b, u0=0.1, name="oil"):
    for i in range(3):
        run(root, f"{name}_hot{i}", t["oil_hot"][i], 7, 7.0, m["hot"], b, u0, 0.85, 50, 18)
        run(root, f"{name}_cool{i}", t["oil_cool"][i], 7, 7.0, m["cool"], b, u0 + 0.12, 0.95, 50, 18)
    for f in t["fans"]:
        D.spin(f, F(b, 0.0), F(b + 1, 0), 10.0)
    for side, (x0, x1) in enumerate((RAD_L, RAD_R)):
        for k, z in enumerate((-260.0, -150.0, -40.0)):
            x = (x0 + x1) / 2 + (k - 1) * 25.0
            run(root, f"{name}_wisp{side}{k}", [(x, RAD_Y[1] + 10.0, z), (x + 10.0, RAD_Y[1] + 120.0, z), (x - 5.0, RAD_Y[1] + 240.0, z)],
                4, 6.0, m["wisp"], b, u0 + 0.1 + 0.04 * k, 0.95, 40, 6)


# ---- 1 what happens -------------------------------------------------------------------------------


def sec1(m, root):
    t = D.transformer(m, root)
    y = D.yard(m, root, t)
    D.tank_mode(t, beat(0), [(F(1, 0), END)])
    show(t["front"], beat(0))
    for i in range(3):
        run(root, f"in{i}", y["hv"][i], 5, 14.0, m["hv"], 0, 0.0 + 0.04 * i, 0.6, 110, 60)
        run(root, f"hv{i}", t["hv"][i], 3, 6.0, m["hv"], 1, 0.0, 0.7, 70, 40)
        run(root, f"lv{i}", t["lv"][i] + y["lv"][i][1:], 9, 7.0, m["lv"], 2, 0.0, 0.8, 90, 50)
    flux(root, m, t, 1)
    p = y["pts"]
    label("230 kV line lands on the gantry", p["gantry"], root, beat(0))
    label("strain insulators", (D.GX - 70.0, 1445.0, D.PZ[0]), root, beat(0))
    label("disconnect switch", p["disconnect"], root, beat(0))
    label("circuit breaker", p["breaker"], root, beat(0))
    label("HV winding", (LXS[0] + 97.0, 300.0, ZC), root, beat(1))
    label("steel core: a changing field", (B, 460.0, ZC), root, beat(1))
    label("LV winding: lower voltage", (LXS[2] - 61.0, 260.0, ZC), root, beat(1))
    label("34.5 kV out", (LVB_X[2], LV_TOP, LVB_Z), root, beat(2))
    label("LV bus", p["lv_bus"], root, beat(2))
    label("cable terminations", p["term"], root, beat(2))
    label("to the campus switchgear", p["house"], root, beat(2))
    camera_path(root, [
        frame((-1750.0, 800.0, -220.0), 1900.0, 0.55, 0.20),
        CUT_VIEW,
        frame((650.0, 420.0, -200.0), 1900.0, 0.50, 0.22),
    ])


# ---- 2 the parts ----------------------------------------------------------------------------------


def sec2(m, root):
    ground(m, root)
    t = D.transformer(m, root)
    D.tank_mode(t, [(0, F(1, 0.05))], [(F(1, 0.05), END)])
    D.front_off(t, 1, 0.05, 0.3, BEATS)
    for i in range(3):
        run(root, f"bush{i}", t["hv"][i][:4], 3, 5.0, m["hv"], 2, 0.05 + 0.05 * i, 0.8, 60, 10)
    label("HV bushings", (HVB_X[1], HV_TOP - 40.0, HVB_Z), root, beat(0))
    label("radiators", (RAD_R[1], 360.0, -40.0), root, beat(0))
    label("conservator: spare oil", (D.CONS[0] + 40.0, D.CONS[2] + 40.0, D.CONS[3]), root, beat(0))
    label("steel tank full of oil", (-250.0, 250.0, 0.0), root, beat(0))
    label("CORE: electrical steel", (B, 460.0, ZC), root, beat(1))
    label("WINDINGS: copper coils", (LXS[0] + 97.0, 300.0, ZC), root, beat(1))
    label("mineral oil", (D.TX0 + 40.0, 470.0, -330.0), root, beat(1))
    label("tap changer", (D.OLTC_X, 470.0, ZC), root, beat(1))
    hx = HVB_X[1]
    label("porcelain shell and sheds", (hx - 30.0, 820.0, HVB_Z), root, beat(2))
    label("copper conductor", (hx, 700.0, HVB_Z), root, beat(2))
    label("paper and foil layers", (hx + 9.0, 620.0, HVB_Z), root, beat(2))
    label("through the grounded lid", (hx + 40.0, D.TY1, HVB_Z + 20.0), root, beat(2))
    camera_path(root, [WHOLE_VIEW, CUT_VIEW, frame((hx, 720.0, HVB_Z), 460.0, 0.25, 0.10)])


# ---- 3 stepping down, in order --------------------------------------------------------------------


def sec3(m, root):
    ground(m, root)
    t = D.transformer(m, root)
    cut_always(t)
    for i in range(3):
        run(root, f"in{i}", t["hv"][i], 3, 10.0, m["hv"], 0, 0.0, 0.5, 110, 60)
        run(root, f"hv1_{i}", t["hv"][i][4:], 3, 5.0, m["hv"], 1, 0.0, 0.7, 60, 40)
        run(root, f"out{i}", t["lv"][i], 12, 5.0, m["lv"], 2, 0.0, 0.8, 60, 20)
    flux(root, m, t, 1)
    oil(root, m, t, 2, 0.2)
    label("1 in through the tall bushings", (HVB_X[0], HV_TOP - 60.0, HVB_Z), root, beat(0))
    label("2 through the many-turn HV winding", (LXS[1] + 97.0, 300.0, ZC), root, beat(0))
    label("3 the core carries the field", (B, 460.0, ZC), root, beat(1))
    label("4 LV winding: lower V, more current", (LVB_X[2], LV_TOP, LVB_Z), root, beat(2))
    label("5 oil carries heat to the radiators", (RAD_R[0] + 60.0, RAD_Y[1], -40.0), root, beat(2))
    camera_path(root, [frame((40.0, 540.0, -200.0), 1200.0, 0.22, 0.12), CORE_VIEW, WIDE_CUT])


# ---- 4 why the turns ratio works ------------------------------------------------------------------


def sec4(m, root):
    c = (0.0, 420.0, 0.0)
    box("bench", (-560.0, 60.0, -160.0), (560.0, 100.0, 120.0), m["dark_steel"], root)
    tc = D.teaching_core(m, root, "tc", c)
    hv, lv = tc["hv"], tc["lv"]
    # beat 0: current in the many-turn coil, flux round the core
    run(root, "hv0", hv, 14, 4.5, m["hv"], 0, 0.0, 0.8, 90, 80)
    run(root, "fx0", tc["flux"], 10, 9.0, m["flux"], 0, 0.15, 0.9, 70, 16)
    # beat 1: one turn of each coil lit
    per = 24
    one_hv = empty("one_hv", root)
    wire("one_hv_w", tc["hv_coil"][per * 9:per * 10 + 1], 5.5, m["hv"], one_hv, 8)
    one_lv = empty("one_lv", root)
    wire("one_lv_w", tc["lv_coil"][0:per + 1], 15.0, m["lv"], one_lv, 10)
    show(one_hv, [(F(1, 0.15), F(2, 0))])
    show(one_lv, [(F(1, 0.35), F(2, 0))])
    run(root, "fx1", tc["flux"], 10, 9.0, m["flux"], 1, 0.0, 0.8, 70, 16)
    # beat 2: few big beads in on the HV side, many on the LV side
    run(root, "hv2", hv, 4, 9.0, m["hv"], 2, 0.0, 0.6, 150, 80)
    run(root, "lv2", lv, 24, 6.0, m["lv"], 2, 0.05, 0.85, 50, 40)
    run(root, "fx2", tc["flux"], 8, 9.0, m["flux"], 2, 0.0, 0.8, 70, 16)
    lx0, lx1 = tc["lxs"]
    label("AC in: 20 turns", (lx0 - 150.0, c[1] + tc["H"] - 8.0, c[2]), root, beat(0))
    label("changing field in the core", (0.0, c[1] + tc["H"] - tc["r"], tc["r"]), root, beat(0))
    label("2 turns share the same field", (lx1 + 70.0, c[1], c[2]), root, beat(0))
    label("one turn: some volts", tc["hv_coil"][per * 9 + 6], root, [(F(1, 0.15), F(2, 0))])
    label("one turn: the same volts", tc["lv_coil"][6], root, [(F(1, 0.35), F(2, 0))])
    label("20 turns: 10x the voltage", (lx0, c[1] - 120.0, c[2] + 60.0), root, beat(2))
    label("2 turns: 10x the current", (lx1, c[1] - 120.0, c[2] + 70.0), root, beat(2))
    label("power in = power out (less losses)", (0.0, c[1] - tc["H"] + tc["r"], tc["r"]), root, beat(2))
    camera_path(root, [
        frame((0.0, 420.0, 0.0), 1050.0, 0.30, 0.14),
        frame((0.0, 420.0, 0.0), 900.0, 0.22, 0.10),
        frame((0.0, 420.0, 0.0), 1050.0, 0.30, 0.14),
    ])


# ---- 5 losses and cooling -------------------------------------------------------------------------


def sec5(m, root):
    ground(m, root)
    t = D.transformer(m, root)
    cut_always(t)
    show(t["hot_core"], [(F(0, 0.1), F(1, 0))])
    show(t["hot_cu"], [(F(1, 0.1), F(2, 0))])
    flux(root, m, t, 0, name="fx0")
    for i in range(3):
        run(root, f"cu{i}", t["hv"][i][4:], 6, 6.0, m["hv"], 1, 0.0, 0.8, 60, 40)
        run(root, f"culv{i}", t["lv"][i][:2], 8, 5.0, m["lv"], 1, 0.0, 0.8, 30, 6)
    oil(root, m, t, 2, 0.05)
    label("core loss: heat in the steel", (B, 460.0, ZC), root, beat(0))
    label("there all day, even at no load", (LXS[2], 300.0, ZC), root, beat(0))
    label("copper loss: resistance", (LXS[0] + 97.0, 300.0, ZC), root, beat(1))
    label("rises with the load", (LXS[2] - 61.0, 260.0, ZC), root, beat(1))
    label("oil: insulates, carries heat", (LXS[2] + 80.0, 470.0, ZC), root, beat(2))
    label("radiator panels", (RAD_R[1], 360.0, -40.0), root, beat(2))
    label("fans", (RAD_R[0] + 60.0, RAD_Y[0] - 22.0, -90.0), root, beat(2))
    label("over 99% of the power passes", (-250.0, D.TY1, -170.0), root, beat(2))
    camera_path(root, [CORE_VIEW, CORE_VIEW, WIDE_CUT])


# ---- 6 the lead time problem ----------------------------------------------------------------------

WK_X0, WK_UNIT = -620.0, 7.5
WK_Z = (170.0, 270.0, 370.0, 470.0)


def sec6(m, root):
    ground(m, root, -1200.0, 1200.0, -800.0, 900.0)
    t = D.transformer(m, root)
    whole_always(t)
    for k, z in enumerate(WK_Z):
        D.week_ruler(m, root, WK_X0, 8.0, z, 156, WK_UNIT, f"ruler{k}")
    rows = [(50, "w21", 0), (120, "w24", 1), (128, "w25", 2), (144, "wgsu", 2)]
    ends = []
    for k, (wk, mt, b) in enumerate(rows):
        u0, u1 = (0.05, 0.55) if k < 3 else (0.25, 0.75)
        ends.append(D.week_row(m, root, WK_X0, 8.0, WK_Z[k], wk, WK_UNIT, m[mt], f"row{k}", F(b, u0), F(b, u1), END))
    label("2021: ~50 weeks", ends[0], root, [(F(0, 0.5), END)])
    label("one tick = one year", (WK_X0 + WK_UNIT * 52, 68.0, WK_Z[0]), root, beat(0))
    label("2024: ~120 weeks", ends[1], root, [(F(1, 0.5), END)])
    label("more than doubled", (WK_X0 + WK_UNIT * 104, 68.0, WK_Z[1]), root, beat(1))
    label("Q2 2025: ~128 weeks", ends[2], root, [(F(2, 0.5), END)])
    label("step-up units: ~144 weeks", ends[3], root, [(F(2, 0.7), END)])
    label("custom-built for its site", (-250.0, 420.0, 0.0), root, beat(2))
    v = frame((-40.0, 60.0, 330.0), 1250.0, 0.12, 0.78)
    camera_path(root, [v, v, v])


# ---- 7 electrical steel ---------------------------------------------------------------------------

COIL = (-700.0, 160.0, -100.0)


def sec7(m, root):
    ground(m, root, -2600.0, 2000.0, -1200.0, 900.0)
    # beat 0: a coil of grain-oriented strip unrolling along x; the grains are long and lined up
    cx, cy, cz = COIL
    D.join([tube("coil_body", (cx, cy, cz - 120.0), (cx, cy, cz + 120.0), 150.0, m["steel_plate"], root, 48),
                   tube("coil_eye", (cx, cy, cz + 120.0), (cx, cy, cz + 121.0), 60.0, m["dark_steel"], root, 32)], "coil_m")
    box("coil_saddle", (cx - 130.0, 0.0, cz - 120.0), (cx + 130.0, 40.0, cz + 120.0), m["dark_steel"], root)
    sx0, sx1 = cx, 600.0
    sy = 12.0
    tiles = []
    k = 0
    for row in range(8):
        z0 = cz - 120.0 + 30.0 * row
        x = sx0 + (row % 3) * 37.0 - 60.0
        while x < sx1:
            L = 150.0 + 40.0 * ((row * 7 + k) % 3)
            xa, xb = max(x, sx0), min(x + L, sx1)
            if xb > xa + 5:
                mt = m[("grain_a", "grain_b", "grain_c")[(row + k) % 3]]
                tiles.append(box(f"grain{row}_{k}", (xa, sy, z0), (xb - 2.0, sy + 4.0, z0 + 28.0), mt, root))
            x += L
            k += 1
    D.join(tiles, "strip_grains")
    box("strip_table", (sx0, 0.0, cz - 125.0), (sx1, sy, cz + 125.0), m["dark_steel"], root)
    tube("strip_wrap", (cx, cy - 150.0, cz - 120.0), (cx, cy - 150.0, cz + 120.0), 4.0, m["steel_plate"], root, 8)
    for j, z in enumerate((cz - 80.0, cz - 10.0, cz + 60.0)):
        run(root, f"field{j}", [(sx0 + 20.0, sy + 10.0, z), (sx1 - 10.0, sy + 10.0, z)], 6, 7.0, m["flux"], 0, 0.05 + 0.05 * j, 0.8, 60, 4)
    # beat 1: sheets cut and stacked into a core (packets drop into place one by one)
    cc = (1300.0, 40.0, -100.0)
    plates = 8
    W, H, r = 200.0, 260.0, 40.0
    for k in range(plates):
        g = empty(f"pk{k}", root)
        za = cc[2] - r + 2 * r * k / plates
        zb = za + 2 * r / plates - 1.0
        mt = m["core_a"] if k % 2 == 0 else m["core_b"]
        parts = []
        for j, lx in enumerate((cc[0] - W, cc[0] + W)):
            parts.append(box(f"pk{k}_l{j}", (lx - r, cc[1] + 2 * r, za), (lx + r, cc[1] + 2 * H - 2 * r, zb), mt, g))
        parts.append(box(f"pk{k}_t", (cc[0] - W - r, cc[1] + 2 * H - 2 * r, za), (cc[0] + W + r, cc[1] + 2 * H, zb), mt, g))
        parts.append(box(f"pk{k}_b", (cc[0] - W - r, cc[1], za), (cc[0] + W + r, cc[1] + 2 * r, zb), mt, g))
        D.join(parts, f"pk{k}_m")
        f0, f1 = F(1, 0.05 + 0.08 * k), F(1, 0.05 + 0.08 * k + 0.12)
        key(g, f0, "location", P(0.0, 500.0, 300.0), linear=True)
        key(g, f1, "location", P(0.0, 0.0, 0.0), linear=True)
        show(g, [(f0, END)])
    box("pk_base", (cc[0] - W - r - 40.0, -2.0, cc[2] - r - 40.0), (cc[0] + W + r + 40.0, cc[1], cc[2] + r + 40.0), m["dark_steel"], root)
    # beat 2: one mill feeding coils down a single road to the core plant
    mx = -2000.0
    mp = [box("mill", (mx - 260.0, 0.0, -400.0), (mx + 260.0, 360.0, 100.0), m["brick"], root),
          box("mill_roof", (mx - 280.0, 360.0, -420.0), (mx + 280.0, 390.0, 120.0), m["roof"], root)]
    for k, x in enumerate((mx - 160.0, mx - 40.0)):
        mp.append(tube(f"stack{k}", (x, 390.0, -300.0), (x, 820.0, -300.0), 28.0, m["concrete"], root, 16))
    mp.append(box("mill_door", (mx + 60.0, 0.0, 100.0), (mx + 200.0, 220.0, 104.0), m["door"], root))
    D.join(mp, "mill_m")
    road = [(mx + 200.0, 4.0, 200.0), (cx - 200.0, 4.0, 200.0), (cx, 4.0, 200.0), (cc[0] - 300.0, 4.0, 200.0)]
    box("road", (mx + 150.0, -2.0, 160.0), (cc[0] - 280.0, 3.0, 240.0), m["concrete"], root)
    for k in range(5):
        e = empty(f"truck{k}", root)
        D.ring_x(f"truck{k}_coil", -30.0 + road[0][0], 30.0 + road[0][0], 50.0, 200.0, 18.0, 45.0, m["steel_plate"], e, 20)
        box(f"truck{k}_bed", (road[0][0] - 60.0, 2.0, 170.0), (road[0][0] + 60.0, 8.0, 230.0), m["dark_steel"], e)
        f0 = F(2, 0.04 + 0.17 * k)
        fly(e, [(0, 0, 0), (road[-1][0] - road[0][0], 0, 0)], f0, f0 + 150, 4)
        show(e, [(f0, min(f0 + 150, END))])
    label("grain-oriented electrical steel", (cx + 400.0, sy + 4.0, cz + 100.0), root, beat(0))
    label("crystals lined up along the strip", (200.0, sy + 4.0, cz - 50.0), root, beat(0))
    label("the field runs along the grain", (sx1 - 60.0, sy + 10.0, cz - 10.0), root, beat(0))
    label("cut into thin sheets", (cc[0] - W, cc[1] + H, cc[2] + r), root, beat(1))
    label("stacked into the core", (cc[0], cc[1] + 2 * H, cc[2]), root, beat(1))
    label("few mills make it", (mx, 390.0, 0.0), root, beat(2))
    label("US: Cleveland-Cliffs, the domestic producer", (mx + 100.0, 220.0, 104.0), root, beat(2))
    label("one supply for many transformers", (-200.0, 60.0, 200.0), root, beat(2))
    camera_path(root, [
        frame((-120.0, 60.0, -80.0), 1500.0, 0.25, 0.55),
        frame((1300.0, 300.0, -100.0), 900.0, 0.35, 0.25),
        frame((-500.0, 250.0, 0.0), 3000.0, 0.35, 0.35),
    ])


# ---- 8 who makes it -------------------------------------------------------------------------------

MAKERS = [("Hitachi Energy", 0), ("Siemens Energy", 0), ("GE Vernova (GEV)", 0),
          ("HD Hyundai Electric", 1), ("Hyosung Heavy Industries", 1), ("Eaton (ETN)", 1)]
HARBOUR = 6200.0


def sec8(m, root):
    ground(m, root, -2200.0, 3600.0, -1000.0, 800.0)
    for k, (maker, b) in enumerate(MAKERS):
        x = -1500.0 + 600.0 * (k % 3) + (0.0 if b == 0 else 1900.0)
        z = 0.0
        box(f"plinth{k}", (x - 290.0, 0.0, z - 260.0), (x + 290.0, 20.0, z + 40.0), m["concrete"], root)
        D.plain_transformer(m, root, (x, 20.0, z), f"u{k}", 0.75, 240.0 + 40.0 * (k % 3))
        label(maker, (x, 360.0, z), root, beat(b))
    # beat 2: a heavy-lift ship brings a unit in to the dock
    box("water", (HARBOUR - 1800.0, -40.0, -1600.0), (HARBOUR + 2600.0, -20.0, 600.0), m["water"], root)
    box("dock", (HARBOUR - 2200.0, -40.0, -1600.0), (HARBOUR - 1800.0, 60.0, 600.0), m["concrete"], root)
    sh = D.ship(m, root, (HARBOUR + 300.0, -40.0, -200.0), "ship", 0.9)
    D.plain_transformer(m, sh, (HARBOUR + 300.0, 194.0, -260.0), "cargo", 0.6, 220.0)
    key(sh, F(2, 0.0), "location", P(900.0, 0.0, 0.0), linear=True)
    key(sh, F(2, 0.85), "location", P(0.0, 0.0, 0.0), linear=True)
    label("most large US units are imported", (HARBOUR + 300.0, 450.0, -260.0), root, beat(2))
    label("heavy-lift ship", (HARBOUR - 400.0, 300.0, -230.0), root, beat(2))
    label("US dock", (HARBOUR - 2000.0, 60.0, 0.0), root, beat(2))
    camera_path(root, [
        frame((-900.0, 280.0, -100.0), 1900.0, 0.30, 0.22),
        frame((1000.0, 280.0, -100.0), 1900.0, 0.30, 0.22),
        frame((HARBOUR - 300.0, 250.0, -300.0), 2900.0, 0.35, 0.25),
    ])


# ---- 9 chokepoints and risks ----------------------------------------------------------------------

UNITS_X = 3200.0


def sec9(m, root):
    ground(m, root, -1400.0, 5000.0, -1200.0, 1000.0)
    # beat 0: one unit and a row of weeks two to three years long
    D.plain_transformer(m, root, (0.0, 0.0, -100.0), "lt", 1.0, 300.0)
    D.week_ruler(m, root, -620.0, 8.0, 260.0, 156, 7.5, "lt_ruler")
    end0 = D.week_row(m, root, -620.0, 8.0, 260.0, 128, 7.5, m["w25"], "lt_row", F(0, 0.05), F(0, 0.6), F(1, 0))
    D.week_row(m, root, -620.0, 8.0, 350.0, 144, 7.5, m["wgsu"], "lt_gsu", F(0, 0.3), F(0, 0.8), F(1, 0))
    # beat 1: three units, each built to its site's voltages, and an empty spare plinth
    for k, h in enumerate((200.0, 320.0, 440.0)):
        x = UNITS_X - 900.0 + 600.0 * k
        box(f"cp{k}", (x - 280.0, 0.0, -380.0), (x + 280.0, 20.0, 40.0), m["concrete"], root)
        D.plain_transformer(m, root, (x, 20.0, -100.0), f"cu{k}", 0.7, h)
    xs = UNITS_X + 900.0
    box("spare_plinth", (xs - 280.0, 0.0, -380.0), (xs + 280.0, 20.0, 40.0), m["concrete"], root)
    D.join([tube("x_a", (xs - 160.0, 26.0, -300.0), (xs + 160.0, 26.0, -20.0), 10.0, m["red"], root, 8),
            tube("x_b", (xs - 160.0, 26.0, -20.0), (xs + 160.0, 26.0, -300.0), 10.0, m["red"], root, 8)], "spare_x")
    # beat 2: a ship held at a tariff gate before the dock
    hx = 7600.0
    box("water", (hx - 1500.0, -40.0, -1600.0), (hx + 2600.0, -20.0, 600.0), m["water"], root)
    box("dock", (hx - 2000.0, -40.0, -1600.0), (hx - 1500.0, 60.0, 600.0), m["concrete"], root)
    sh = D.ship(m, root, (hx + 400.0, -40.0, -300.0), "ship", 0.9)
    D.plain_transformer(m, sh, (hx + 400.0, 194.0, -360.0), "cargo", 0.6, 220.0)
    key(sh, F(2, 0.0), "location", P(900.0, 0.0, 0.0), linear=True)
    key(sh, F(2, 0.45), "location", P(250.0, 0.0, 0.0), linear=True)
    key(sh, F(2, 0.95), "location", P(150.0, 0.0, 0.0), linear=True)
    gx = hx - 700.0
    gp = [tube("gate_post_a", (gx, -20.0, 300.0), (gx, 420.0, 300.0), 22.0, m["white"], root, 12),
          tube("gate_post_b", (gx, -20.0, -1300.0), (gx, 420.0, -1300.0), 22.0, m["white"], root, 12)]
    D.join(gp, "gate_posts")
    bar = empty("gate_bar", root)
    stripes = [box(f"gate_s{k}", (gx - 14.0, 360.0, 300.0 - 100.0 * (k + 1)), (gx + 14.0, 390.0, 300.0 - 100.0 * k),
                   m["red"] if k % 2 == 0 else m["white"], bar) for k in range(16)]
    D.join(stripes, "gate_bar_m")
    key(bar, F(2, 0.0), "location", P(0.0, 500.0, 0.0), linear=True)
    key(bar, F(2, 0.3), "location", P(0.0, 0.0, 0.0), linear=True)
    label("LEAD TIME: two to three years", end0, root, beat(0))
    label("step-up units wait longer", (-620.0 + 7.5 * 144, 34.0, 332.0), root, beat(0))
    label("each built for its site's voltages", (UNITS_X - 300.0, 400.0, -240.0), root, beat(1))
    label("no spare to swap in", (xs, 30.0, -160.0), root, beat(1))
    label("tariffs on imports", (gx, 420.0, -500.0), root, beat(2))
    label("expected to worsen lead times", (hx + 500.0, 450.0, -360.0), root, beat(2))
    camera_path(root, [
        frame((0.0, 220.0, 120.0), 1500.0, 0.20, 0.40),
        frame((UNITS_X + 200.0, 260.0, -150.0), 2500.0, 0.25, 0.25),
        frame((hx - 100.0, 250.0, -400.0), 3000.0, 0.40, 0.25),
    ])


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}


def build(n):
    m, root = setup(n)
    SECTIONS[n](m, root)
    finish(f"section_{n}")


if __name__ == "__main__":
    build(int(sys.argv[sys.argv.index("--") + 1]))
