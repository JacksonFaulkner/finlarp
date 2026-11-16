"""The SUBSTATION node page's overview, in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/power_substation_overview.py

Writes blender/power_substation_overview.blend and assets/power_substation_overview.glb. One beat is 8 s.

The scene is a substation yard (power_substation_detail.yard): the 230 kV line arriving from a lattice
tower, the dead-end gantry, surge arresters, a disconnect switch, a dead-tank breaker, bus posts, and
the power transformer (power_substation_detail.transformer), whose LV bus runs to cable terminations
and the switchgear house. From beat 2 the transformer's front wall lifts away and its walls and
bushings are shown cut open through the core.

Beats (match the seven beats in diagrams_nodes/power/substation/overview.rs):
  0 yard       power rides the line in, through the breaker, into the transformer and out to the house
  1 unit       the transformer whole: tank, bushings, radiators, conservator
  2 cut open   the front lifts away: core, LV and HV windings, oil, tap changer
  3 flux       cyan flux beads loop round the core, reversing half way (AC)
  4 amps       a few big yellow beads in at high voltage, many small orange ones out at low voltage
  5 heat       the core glows (core loss), then the windings (copper loss); oil carries heat to the radiators
  6 wait       lead-time rows grow in front of the unit: ~50, ~120, ~128 weeks (GSU ~144)

power_substation_zooms.py rebuilds this scene with its own camera and tags (it swaps LABEL and CAMERA).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start  # noqa: E402
from pbr_kit import empty  # noqa: E402
import power_substation_detail as D  # noqa: E402
from power_substation_detail import finish, frame, camera_path, run, runs, ZC, LXS, HVB_X, LVB_X, HV_TOP, LV_TOP  # noqa: E402

PAGE = D.PAGE
NAME = "overview"
BEATS = 7

# lead-time rows (beat 6): x start, cm per week, rows' z
WK_X0, WK_UNIT = -560.0, 7.0
WK_Z = (160.0, 250.0, 340.0, 430.0)

LABEL = label
CAMERA = camera_path


def lead_rows(m, root, b, end):
    """The four lead-time rows in front of the unit, growing through beat b. Returns their end points."""
    ruler = empty("wk_ruler", root)
    for k, z in enumerate(WK_Z):
        D.week_ruler(m, ruler, WK_X0, 8.0, z, 144, WK_UNIT, f"wk_ruler{k}")
    show(ruler, [(F(b, 0), end)])
    rows = [(50, "w21", 0.03, 0.2), (120, "w24", 0.28, 0.5), (128, "w25", 0.58, 0.8), (144, "wgsu", 0.6, 0.85)]
    ends = []
    for k, (weeks, mt, u0, u1) in enumerate(rows):
        ends.append(D.week_row(m, root, WK_X0, 8.0, WK_Z[k], weeks, WK_UNIT, m[mt], f"wk{k}", F(b, u0), F(b, u1), end))
    return ends


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    D.materials(m)
    t = D.transformer(m, root)
    y = D.yard(m, root, t)
    end = F(BEATS, 0)

    D.tank_mode(t, [(0, F(2, 0.05)), (F(6, 0), end)], [(F(2, 0.05), F(6, 0))])
    D.front_off(t, 2, 0.05, 0.35, BEATS, back_at=6)
    show(t["hot_core"], [(F(5, 0.0), F(5, 0.45))])
    show(t["hot_cu"], [(F(5, 0.3), F(5, 0.72))])

    # beat 0: power rides in along the line, through the breaker, to the bushings; out to the house
    for i in range(3):
        run(root, f"y_hv{i}", y["hv"][i], 4, 14.0, m["hv"], 0, 0.0 + 0.04 * i, 0.55 + 0.04 * i, 70, 60)
        run(root, f"y_lv{i}", y["lv"][i], 6, 9.0, m["lv"], 0, 0.15 + 0.03 * i, 0.8, 70, 30)
    # beat 1: beads arrive at the HV bushings and leave the LV bushings
    for i in range(3):
        run(root, f"u_hv{i}", y["hv"][i][-15:], 3, 9.0, m["hv"], 1, 0.1, 0.7, 60, 16)
        run(root, f"u_lv{i}", y["lv"][i][:6], 4, 6.0, m["lv"], 1, 0.15, 0.8, 50, 12)
    # beat 3: flux round the core, reversing half way; a trickle of current in the HV discs
    for k in range(2):
        run(root, f"fx_a{k}", t["flux"][k], 7, 7.0, m["flux"], 3, 0.0, 0.3, 50, 24)
        run(root, f"fx_b{k}", t["flux_rev"][k], 7, 7.0, m["flux"], 3, 0.52, 0.82, 50, 24)
    for i in range(3):
        run(root, f"fx_hv{i}", t["hv"][i][4:], 3, 5.0, m["hv"], 3, 0.0, 0.7, 60, 40)
    # beat 4: few big beads in at high voltage, many small ones out at low voltage
    for i in range(3):
        run(root, f"a_hv{i}", t["hv"][i], 3, 11.0, m["hv"], 4, 0.0, 0.45, 110, 60)
        run(root, f"a_lv{i}", t["lv"][i] + y["lv"][i][1:], 14, 5.0, m["lv"], 4, 0.15, 0.85, 110, 60)
    # beat 5: oil carries the heat up the ducts, to the radiators, down their panels and back
    for i in range(3):
        run(root, f"o_hot{i}", t["oil_hot"][i], 6, 7.0, m["hot"], 5, 0.42, 0.85, 50, 18)
        run(root, f"o_cool{i}", t["oil_cool"][i], 6, 7.0, m["cool"], 5, 0.55, 0.95, 50, 18)
    for k, f in enumerate(t["fans"]):
        D.spin(f, F(5, 0.45), F(6, 0), 10.0)
    for side, (x0, x1) in enumerate((D.RAD_L, D.RAD_R)):
        for k, z in enumerate((-260.0, -150.0, -40.0)):
            x = (x0 + x1) / 2 + (k - 1) * 25.0
            run(root, f"wisp{side}{k}", [(x, D.RAD_Y[1] + 10.0, z), (x + 10.0, D.RAD_Y[1] + 120.0, z), (x - 5.0, D.RAD_Y[1] + 240.0, z)],
                4, 6.0, m["wisp"], 5, 0.5 + 0.04 * k, 0.95, 40, 6)
    # beat 6: lead times
    ends = lead_rows(m, root, 6, end)

    T = D.TY1
    tags = {
        0: [("230 kV line in", y["pts"]["mid_line"]), ("dead-end gantry", y["pts"]["gantry"]),
            ("circuit breaker", y["pts"]["breaker"]), ("power transformer", (0.0, T, -40.0)),
            ("34.5 kV out to the campus", y["pts"]["house"])],
        1: [("HV bushings", (HVB_X[1], HV_TOP - 40.0, D.HVB_Z)), ("LV bushings", (LVB_X[0], LV_TOP - 30.0, D.LVB_Z)),
            ("radiators", (D.RAD_R[1], 360.0, -40.0)), ("conservator: spare oil", (D.CONS[0] + 40.0, D.CONS[2] + 40.0, D.CONS[3])),
            ("steel tank full of oil", (-250.0, 250.0, 0.0))],
        2: [("laminated steel core", (LXS[1], 460.0, ZC)), ("LV winding (inner)", (LXS[0] - 61.0, 300.0, ZC)),
            ("HV winding (outer)", (LXS[2] + 97.0, 240.0, ZC)), ("tap changer", (D.OLTC_X, 470.0, ZC))],
        3: [("magnetic flux in the core", (LXS[1], 300.0, ZC)), ("HV winding drives it", (LXS[0] + 97.0, 300.0, ZC)),
            ("LV winding picks it up", (LXS[2] - 61.0, 260.0, ZC))],
        4: [("high voltage, low current in", (HVB_X[0], HV_TOP, D.HVB_Z)), ("low voltage, high current out", (LVB_X[2], LV_TOP, D.LVB_Z)),
            ("230 kV to 34.5 kV", (LXS[1], 300.0, ZC))],
        5: [("core loss: always on", (LXS[1], 460.0, ZC)), ("copper loss: rises with load", (LXS[0] + 97.0, 250.0, ZC)),
            ("hot oil to the radiators", (D.RAD_R[0] + 60.0, D.RAD_Y[1], -40.0)), ("fans", (D.RAD_R[0] + 60.0, D.RAD_Y[0] - 22.0, -90.0))],
    }
    for i, items in tags.items():
        for text, pos in items:
            LABEL(text, pos, root, beat(i))
    LABEL("2021: ~50 weeks", ends[0], root, [(F(6, 0.12), F(7, 0))])
    LABEL("2024: ~120 weeks", ends[1], root, [(F(6, 0.42), F(7, 0))])
    LABEL("2025: ~128 weeks", ends[2], root, [(F(6, 0.72), F(7, 0))])
    LABEL("step-up units: ~144", ends[3], root, [(F(6, 0.8), F(7, 0))])

    CAMERA(root, POSES)
    return root


POSES = [
    frame((-1250.0, 500.0, -250.0), 3300.0, 0.62, 0.30, pad=1.0),
    frame((20.0, 520.0, -170.0), 1400.0, 0.38, 0.22),
    frame((30.0, 340.0, ZC), 1050.0, 0.22, 0.12),
    frame((0.0, 300.0, ZC), 820.0, 0.12, 0.08),
    frame((40.0, 560.0, -190.0), 1250.0, 0.22, 0.14),
    frame((30.0, 400.0, -170.0), 1450.0, 0.30, 0.18),
    frame((0.0, 380.0, 60.0), 1500.0, 0.28, 0.42),
]


if __name__ == "__main__":
    build()
    finish(NAME)
