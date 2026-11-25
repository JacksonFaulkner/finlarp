"""The COOLING TOWER page's overview (NETWORK+COOL tab); it also covers HEAT OUT, the heat leaving
for the outdoor air.

    blender -b --factory-startup --python tools/pbr3d/blender/net_cooling_tower_overview.py

Writes assets/net_cooling_tower_overview.glb. One beat is 8 s.

Beats (match diagrams_nodes/netcool/cooling_tower/overview.rs):
  0 site       chiller plant + wet tower; warm water out, cooled water back
  1 spray      warm water up to the header and out of the nozzles
  2 fill       water films on the fill; air in through the louvers, rising through
  3 fan        the fan pulls the air up; ~1% evaporates; plume
  4 drift      eliminators catch droplets, let vapour pass
  5 water      make-up meter spins; blowdown drains minerals
  6 heat out   every flow at once; the heat leaves as vapour into the sky
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net_cooling_tower_detail as T  # noqa: E402
from net_cooling_tower_detail import show, frame, camera_path, blink, C, FANC, DECK, FILL, DRIFT, SPRAY  # noqa: E402

NAME = "overview"
BEATS = 7


def build():
    m, root = T.setup(NAME, BEATS)
    s = T.scene(m, root)
    for k in range(BEATS):
        blink(s["leds"], k, [0, 2, 4, 6], n=8, on=0.7)
    T.loop(m, root, [0, 1, 5, 6])
    T.spray(m, root, [1, 6])
    show(s["films"], T.span(2, 0.0, 5, 0.0) + T.span(6, 0.0, 7, 0.0))
    T.falling(m, root, [2, 3, 6])
    T.air(m, root, [2, 3, 6])
    C.spin(s["fan"], list(range(BEATS)), turns=4.0)
    T.plume(m, root, [3, 6])
    T.drift_drops(m, root, [4])
    T.makeup(m, root, s, [5])
    T.plume(m, root, [6], n=12, h=260.0, name="sky")
    T.tags(root, [
        [("chiller condenser", T.PLANT_TAG), ("warm water out ~35 C", (-10.0, 150.0, -90.0)), ("cooled ~29 C back", (0.0, 14.0, -40.0)),
         ("wet cooling tower", T.TOWER_TAG)],
        [("spray header", T.SPRAY_TAG), ("nozzles spread it", (FANC[0], SPRAY - 6.0, -4.0))],
        [("fill: thin water films", T.FILL_TAG), ("air in through louvers", T.LOUV_TAG), ("cooled water to the basin", T.BASIN_TAG)],
        [("fan pulls air up", T.FAN_TAG), ("~1% of the water evaporates", T.SKY_TAG)],
        [("drift eliminators", T.DRIFT_TAG), ("droplets fall back", (T.TX0 + 60.0, SPRAY, -3.0))],
        [("make-up water meter", T.METER_TAG), ("blowdown sheds minerals", T.BD_TAG), ("~1.5-2 L per kWh of heat", T.SKY_TAG)],
        [("HEAT OUT: into the air", (FANC[0], DECK + 300.0, FANC[2])), ("as water vapour", T.SKY_TAG), ("from the chiller", T.PLANT_TAG)],
    ])
    camera_path(root, [
        T.SITE,
        frame((FANC[0], SPRAY, -40.0), 280.0, 0.15, 0.20),
        frame((FANC[0], 130.0, -40.0), 300.0, 0.10, 0.12),
        [(0.0, frame((FANC[0], 230.0, -80.0), 330.0, 0.25, 0.30)), (0.55, frame((FANC[0], 280.0, -90.0), 380.0, -0.15, 0.50))],
        frame((FANC[0], (SPRAY + DRIFT[1]) / 2, -20.0), 200.0, 0.10, 0.15),
        frame((T.TX1 + 10.0, 50.0, -40.0), 260.0, 0.30, 0.30),
        frame((60.0, 230.0, -90.0), 720.0, -0.25, 0.30, pad=1.0),
    ])


if __name__ == "__main__":
    build()
    T.N.finish(NAME, page=T.PAGE)
