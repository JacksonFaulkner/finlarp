"""The UPS node page's overview (POWER tab), in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/power_ups_overview.py

Writes blender/power_ups_overview.blend and assets/power_ups_overview.glb. One beat is 8 s.

The whole site, cut open at the front (power_ups_detail.plant): the utility line on its pole, the
diesel generator on its fuel tank, the transfer switch, the UPS lineup (rectifier, DC link, inverter,
static bypass), the lithium-ion battery cabinets and the racks. Power is beads riding the cables:
yellow AC from the utility, cyan DC, orange battery power, green generator power.

Beats (match the seven beats in diagrams_nodes/power/ups/overview.rs, and the UPS overview of the
old rig in diagrams_pwr_nodes.rs):
  0 normal     utility -> transfer switch -> rectifier -> DC link -> inverter -> racks
  1 charged    the DC link keeps the battery cabinets topped up; module LEDs fill
  2 outage     the utility line goes red; the batteries feed the DC link, the inverter never stops
  3 runtime    the battery modules drain, LED by LED
  4 genset     the engine starts: pistons, crank, rotor, fan turn; exhaust rises
  5 transfer   the transfer switch's blade swings to the generator; green power in; batteries recharge
  6 losses     normal running again; heat rises off the rectifier and inverter (3-5% lost)

A hidden eighth beat (7, past the overview's end) runs ECO mode, utility power through the static
bypass, for the zooms: power_ups_zooms.py replays beats of this scene under its own camera.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show, ball  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
from pbr_kit import empty  # noqa: E402
import power_ups_detail as D  # noqa: E402
from power_ups_detail import frame, camera_path, flow, rise, soc, engine_run, drops_flow  # noqa: E402

PAGE = "power_ups"
NAME = "overview"
BEATS = 7
OUT = 0.12  # fraction of beat 2 when the utility drops
XFER = 0.30  # fraction of beat 5 when the transfer switch moves

# swapped by power_ups_zooms.py
LABEL = label
CAMERA = camera_path


def runs(*beats, u0=0.0, u1=0.85):
    return [(b, u0, u1) for b in beats]


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = D.materials()
    S = D.plant(m, root)
    at, gp, P_ = S["ats"], S["gen"], S["paths"]

    # ---- state over time ----
    show(S["dead"], [(F(2, OUT), F(6, 0))])
    show(at["blade_u"], [(0, F(5, XFER)), (F(6, 0), F(9, 0))])
    show(at["blade_g"], [(F(5, XFER), F(6, 0))])
    show(at["led_u"], [(0, F(2, OUT)), (F(6, 0), F(9, 0))])
    show(at["led_g"], [(F(4, 0.75), F(6, 0))])
    spark = empty("ats_spark", root)
    ball("ats_spark_b", (at["pv"][0] - 20, 110.0, -18.0), 7.0, m["spark"], spark, 12)
    show(spark, [(F(5, XFER - 0.03), F(5, XFER + 0.04))])
    engine_run(gp, F(4, 0.12), F(6, 0))
    rise(root, "smoke4", gp["stack"], m["smoke"], [(4, 0.14, 0.9)], n=10, size=9.0, height=150, spread=(20, 10), seed=1)
    rise(root, "smoke5", gp["stack"], m["smoke"], [(5, 0.0, 0.85)], n=6, size=7.0, height=130, spread=(20, 10), seed=2)
    show(S["ss"]["glow"], [(F(7, 0), F(8, 0))])
    # charge level: topped up in beat 1, drains through the outage, recharges after the transfer
    soc(S["bats"], [(0, 0.72), (F(1, 0.1), 0.72), (F(1, 0.8), 1.0), (F(2, OUT), 1.0), (F(5, XFER), 0.3),
                    (F(6, 0), 0.62), (F(6, 0.7), 1.0), (F(8, 0), 1.0)])

    # ---- the flows ----
    flow(root, "f_util", P_["util"], m["ac"], runs(0, 1, 6) + [(2, 0.0, 0.02)], n=9)
    flow(root, "f_rect", P_["rect"], m["dc"], runs(0, 1, 6) + [(5, XFER + 0.06, 0.9)], n=6)
    flow(root, "f_inv", P_["inv"], m["ac"], runs(0, 1, 2, 3, 4, 5, 6), n=10)
    drops_flow(root, S, m["ac"], runs(0, 1, 2, 3, 4, 5, 6, 7))
    flow(root, "f_charge", P_["charge"], m["dc"], runs(0, 1) + [(5, XFER + 0.1, 0.9)], n=6)
    flow(root, "f_dis", P_["discharge"], m["bat"], [(2, OUT, 0.9), (3, 0.0, 0.9), (4, 0.0, 0.9), (5, 0.0, XFER)], n=7)
    flow(root, "f_gen", P_["gen"], m["gen"], [(5, XFER, 0.9)], n=8)
    flow(root, "f_util7", P_["util_bypass"], m["ac"], runs(7), n=8)
    flow(root, "f_bypass", P_["bypass"], m["ac"], runs(7), n=9)
    for nm, key_ in (("rect", "rect"), ("inv", "inv")):
        for k, h in enumerate(S[key_]["heat"]):
            rise(root, f"heat_{nm}{k}", h, m["heat"], [(6, 0.05, 0.85)], n=9, size=5.0, height=110, spread=(80, 20), seed=k + 3)

    # ---- tags ----
    rc, dl, iv, bt, rk = S["rect"], S["dcl"], S["inv"], S["bats"], S["racks"]
    C = S["C"]
    tags = {
        0: [("utility feed", C["util_drop"][4]), ("diesel generator", (gp["c"][0], 300.0, 0.0)), ("transfer switch", at["top"]),
            ("UPS: AC > DC > AC", dl["top"]), ("racks", rk["top"])],
        1: [("DC link", dl["top"]), ("Li-ion battery cabinets", bt[1]["top"]), ("module LEDs fill: charging", bt[2]["mod"]),
            ("DC to the batteries", C["dc_batt"][7])],
        2: [("utility lost", C["util_drop"][5]), ("batteries take over: no break", C["dc_batt"][7]),
            ("inverter keeps running", iv["top"]), ("racks never notice", rk["top"])],
        3: [("modules draining", bt[0]["mod"]), ("battery DC to the inverter", C["dc_batt"][8]), ("runtime: minutes", bt[2]["top"])],
        4: [("diesel engine: pistons", gp["piston"]), ("alternator spins up", gp["alt"]), ("exhaust", gp["stack"]),
            ("up to speed in ~10 s", gp["panel"])],
        5: [("transfer switch: to generator", at["top"]), ("generator power", C["gen_out"][7]), ("rectifier back on", rc["top"])],
        6: [("rectifier: AC to DC", rc["top"]), ("inverter: DC to AC", iv["top"]), ("heat: 3-5% lost", rc["heat"][1]),
            ("DC link", dl["top"])],
    }
    for i, items in tags.items():
        for text, pos in items:
            LABEL(text, pos, root, beat(i))

    CAMERA(root, POSES)
    return root, S


POSES = [
    frame((-720.0, 170.0, -40.0), 1900.0, 0.30, 0.36, pad=0.86),
    frame((-440.0, 140.0, -30.0), 520.0, 0.30, 0.22),
    frame((-560.0, 220.0, -80.0), 1150.0, 0.28, 0.28, pad=0.95),
    frame((-242.0, 120.0, -20.0), 330.0, 0.32, 0.18),
    frame((D.GX0 + 290.0, 180.0, 0.0), 620.0, 0.26, 0.20),
    frame((-1160.0, 200.0, -20.0), 1080.0, 0.26, 0.24, pad=0.95),
    frame((-620.0, 115.0, -30.0), 380.0, 0.26, 0.16),
]


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
