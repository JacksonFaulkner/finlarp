"""The CHILLER page's overview (NETWORK+COOL tab), in the picture-and-panel template.

    blender -b --factory-startup --python tools/pbr3d/blender/net_chiller_overview.py

Writes assets/net_chiller_overview.glb. One beat is 8 s. The site comes from net_chiller_detail.py
(TRM_CHILLER's hall and cut-open air-cooled chiller).

Beats (match diagrams_nodes/netcool/chiller/overview.rs):
  0 site        hall + chiller; chilled water out, warm water back
  1 evaporator  warm water through the evaporator tubes; refrigerant boils around them
  2 compressor  suction gas into the screw compressor; hot gas leaves it
  3 condenser   hot gas in the V-bank coils; fans spin; heat rises off the deck
  4 valve       liquid through the expansion valve, flashing cold, back to the evaporator
  5 free        cold day: compressor stops, the free-cooling coil does the work
  6 all         the whole loop running, racks blinking
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net_chiller_detail as N  # noqa: E402
from net_chiller_detail import F, show, frame, camera_path, run, blink, CH  # noqa: E402

NAME = "overview"
BEATS = 7


def build():
    m, root = N.setup(NAME, BEATS)
    s = N.scene(m, root)
    p = s["p"]
    for k in range(BEATS):
        blink(s["leds"], k, [0, 2, 4, 6], n=8, on=0.7)
    N.water(m, root, s, [0, 1, 5, 6])
    N.boil(m, root, [1, 6])
    N.refrigerant(m, root, s, [2], ("suc",))
    N.refrigerant(m, root, s, [3], ("dis",))
    N.refrigerant(m, root, s, [4], ("liq",))
    N.refrigerant(m, root, s, [6])
    N.comp_heat(m, root, [2, 6])
    show(p["hot"], N.span(3, 0.2, 4, 0.0) + N.span(6, 0.0, 7, 0.0))
    N.fans_spin(s, [0, 1, 2, 3, 4, 5, 6])
    N.plumes(m, root, [3, 6])
    N.plumes(m, root, [5], n=4, h=40.0, name="plf")
    show(p["free"], N.span(5, 0.1, 6, 0.0))
    run(root, "w_free", N.FREE, 9, 4.0, m["c_supply"], [5], 0.15, 0.8, 50)

    N.tags(root, [
        [("data hall", N.HALL_TAG), ("air-cooled chiller", (180.0, CH.CY1 + 30.0, -60.0)),
         ("chilled water out", (-20.0, 12.0, -150.0)), ("warm water back", (-20.0, 24.0, -120.0))],
        [("evaporator: shell + tubes", N.EVAP_TAG), ("refrigerant boils at ~5 C", (130.0, CH.EV[2] - 14.0, 0.0)),
         ("water leaves colder", (CH.CX0 - 10.0, CH.EV[2] + 8.0, CH.EV[3]))],
        [("screw compressor", N.COMP_TAG), ("cold vapour in", (215.0, CH.EV[2] + 6.0, CH.EV[3])), ("hot gas out ~60-80 C", (270.0, 66.0, -62.0))],
        [("condenser coils", N.COND_TAG), ("fans pull air through", N.FAN_TAG), ("heat to the outdoors", (CH.CX0 + 186.0, CH.CY1 + 70.0, -60.0))],
        [("expansion valve", N.VALVE_TAG), ("pressure drops, liquid flashes cold", (150.0, 56.0, -35.0)), ("back to the evaporator", N.EVAP_TAG)],
        [("free-cooling coil", N.FREE_TAG), ("compressor off", N.COMP_TAG), ("cold air does the work", N.FAN_TAG)],
        [("~3-6 kW of heat per kW", (180.0, CH.CY1 + 30.0, -60.0)), ("racks", N.HALL_TAG), ("air handler coil", N.AHU_TAG)],
    ])
    camera_path(root, [
        N.SITE,
        frame((130.0, 35.0, -50.0), 200.0, 0.10, 0.20),
        frame((255.0, 40.0, -50.0), 150.0, 0.30, 0.25),
        [(0.0, frame((180.0, 110.0, -60.0), 340.0, 0.35, 0.55)), (0.55, frame((180.0, 140.0, -60.0), 320.0, -0.2, 0.75))],
        frame((170.0, 50.0, -40.0), 200.0, -0.15, 0.25),
        frame((180.0, 90.0, -80.0), 330.0, 0.45, 0.40),
        frame((0.0, 60.0, -120.0), 720.0, -0.25, 0.45, pad=1.0),
    ])


if __name__ == "__main__":
    build()
    N.finish(NAME, page=N.PAGE)
