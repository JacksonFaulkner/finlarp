"""The COOLING TOWER page's nine numbered sections. Section N illustrates heading N of
tui/src/screens/diagrams_pages/NET_COOLING_TOWER.txt (the tenth, Sources, is text only). Three beats each.

    blender -b --factory-startup --python tools/pbr3d/blender/net_cooling_tower_sections.py -- <n>

  1 what happens   warm water in; it falls through air; heat out as vapour
  2 the parts      basin + louvers; fill + spray; drift + fan
  3 in order       spray, fill, basin
  4 the physics    latent heat; range and approach; wet bulb
  5 fill and air   fill sheets close up; fan; counterflow
  6 water use      evaporation; blowdown; litres per MW
  7 drift + safety drift blades; blowdown; treatment
  8 who makes it   makers tagged on the site
  9 heat out       wet vs dry; water stress; the plume
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net_cooling_tower_detail as T  # noqa: E402
from net_cooling_tower_detail import show, frame, camera_path, blink, C, FANC, DECK, SPRAY, DRIFT, BY  # noqa: E402

BEATS = 3
B3 = [0, 1, 2]


def site(m, root):
    s = T.scene(m, root)
    for k in range(BEATS):
        blink(s["leds"], k, [0, 2, 4, 6], n=8, on=0.7)
    C.spin(s["fan"], B3, turns=4.0)
    return s


def sec1(m, root):
    s = site(m, root)
    T.loop(m, root, [0, 2])
    T.spray(m, root, [1])
    show(s["films"], T.span(1, 0.0, 3, 0.0))
    T.falling(m, root, [1])
    T.air(m, root, [1])
    T.plume(m, root, [2], h=220.0)
    T.tags(root, [
        [("warm condenser water ~35 C", (-10.0, 150.0, -90.0)), ("tower", T.TOWER_TAG)],
        [("water falls through rising air", T.FILL_TAG), ("air in", T.LOUV_TAG)],
        [("heat leaves as vapour", T.SKY_TAG), ("cooled water back ~29 C", (0.0, 14.0, -40.0))],
    ])
    camera_path(root, [T.SITE, T.TOWER, frame((FANC[0], 260.0, -90.0), 420.0, 0.20, 0.30)])


def sec2(m, root):
    s = site(m, root)
    show(s["films"], T.span(1, 0.0, 3, 0.0))
    T.spray(m, root, [1])
    T.drift_drops(m, root, [2])
    T.tags(root, [
        [("BASIN", T.BASIN_TAG), ("LOUVERS", T.LOUV_TAG)],
        [("FILL", T.FILL_TAG), ("SPRAY NOZZLES", T.SPRAY_TAG)],
        [("DRIFT ELIMINATORS", T.DRIFT_TAG), ("FAN + gearbox", T.FAN_TAG)],
    ])
    camera_path(root, [frame((FANC[0], 60.0, -40.0), 300.0, 0.25, 0.20), frame((FANC[0], 165.0, -40.0), 280.0, 0.10, 0.12),
                       frame((FANC[0], 240.0, -60.0), 300.0, 0.15, 0.30)])


def sec3(m, root):
    s = site(m, root)
    T.loop(m, root, [0])
    T.spray(m, root, [0])
    show(s["films"], T.span(1, 0.0, 3, 0.0))
    T.falling(m, root, [1, 2])
    T.air(m, root, [1])
    T.tags(root, [
        [("1 warm water pumped up", (-10.0, 150.0, -90.0)), ("2 sprayed over the fill", T.SPRAY_TAG)],
        [("3 films meet rising air", T.FILL_TAG), ("4 some evaporates", T.FAN_TAG)],
        [("5 cooled water rains to the basin", T.BASIN_TAG), ("6 pumped back to the chiller", (0.0, 14.0, -40.0))],
    ])
    camera_path(root, [frame((60.0, 150.0, -60.0), 420.0, 0.20, 0.20), T.TOWER, frame((FANC[0], 40.0, -30.0), 280.0, 0.20, 0.15)])


def sec4(m, root):
    d = T.drop_bench(m, root, [0])
    g, t = T.bars(m, root, "temps", -120.0, BY, -40.0, [(105.0, "bar_r", ""), (87.0, "bar_b", ""), (72.0, "bar_g", "")], w=50.0, gap=30.0,
                  unit=2.0)
    T.present(g, T.span(1, 0.0, 3, 0.0))
    T.tags(root, [
        [("latent heat: ~2,400 kJ per kg", d["vap"]), ("the drop cools as it loses vapour", d["below"])],
        [("hot water in ~35 C", t[0]), ("cold water out ~29 C", t[1]), ("wet bulb ~25 C", t[2])],
        [("RANGE: in minus out (~6 C)", t[0]), ("APPROACH: out minus wet bulb (~3-5 C)", t[1])],
    ])
    camera_path(root, [frame((0.0, T.DRP[1], T.DRP[2]), 300.0, 0.20, 0.15), frame((-20.0, BY + 90.0, -40.0), 340.0, 0.15, 0.15),
                       frame((-20.0, BY + 90.0, -40.0), 340.0, -0.2, 0.15)])


def sec5(m, root):
    f = T.fill_bench(m, root)
    show(f["film"], T.span(0, 0.0, 2, 0.0))
    T.fill_flow(m, root, [0, 1])
    T.present(f["g"], T.span(0, 0.0, 2, 0.0))
    s = site(m, root)
    T.air(m, root, [2])
    T.plume(m, root, [2])
    T.tags(root, [
        [("fill: huge wet surface", f["sheet"]), ("films, not drops", f["top"])],
        [("COUNTERFLOW: air up, water down", f["gap"]), ("more surface, closer approach", f["bottom"])],
        [("fan: 100-200 kW on VFD", T.FAN_TAG), ("induced draft: pulls from the top", T.SKY_TAG)],
    ])
    camera_path(root, [frame((0.0, BY + 40.0, T.FB[2]), 250.0, 0.30, 0.20), frame((-30.0, BY, T.FB[2]), 260.0, -0.15, 0.10),
                       frame((FANC[0], 230.0, -80.0), 380.0, 0.20, 0.35)])


def sec6(m, root):
    s = site(m, root)
    T.plume(m, root, [0])
    T.makeup(m, root, s, [1])
    g, t = T.bars(m, root, "lpd", -100.0, BY, -40.0, [(36.0, "bar_b", ""), (90.0, "bar_a", ""), (180.0, "bar_r", "")], w=50.0, gap=30.0)
    T.tags(root, [
        [("~1% evaporates per ~6 C of cooling", T.SKY_TAG), ("each kWh of heat: ~1.5 L", T.FAN_TAG)],
        [("make-up replaces it", T.METER_TAG), ("blowdown drains minerals", T.BD_TAG)],
        [("100 MW of heat: ~3.6M L/day", t[0]), ("1 GW campus: ~36M L/day", t[2]), ("towns use similar", t[1])],
    ])
    camera_path(root, [frame((FANC[0], 260.0, -80.0), 380.0, 0.25, 0.30), frame((T.TX1 + 10.0, 50.0, -40.0), 300.0, 0.30, 0.30),
                       frame((0.0, BY + 90.0, -40.0), 330.0, 0.15, 0.15)])


def sec7(m, root):
    d = T.drift_bench(m, root)
    T.drift_flow(m, root, [0])
    s = site(m, root)
    T.makeup(m, root, s, [1, 2])
    T.loop(m, root, [2])
    T.tags(root, [
        [("drift eliminators catch droplets", d["blade"]), ("drift: ~0.0005-0.001% of flow", d["above"])],
        [("blowdown: keeps minerals in check", T.BD_TAG), ("scale + corrosion if skipped", T.BASIN_TAG)],
        [("water treatment: biocide, inhibitors", T.METER_TAG), ("Legionella: ASHRAE 188 plans", T.BASIN_TAG)],
    ])
    camera_path(root, [frame((0.0, T.DRB[1], T.DRB[2]), 300.0, 0.20, 0.15), frame((T.TX0 - 10.0, 40.0, -20.0), 220.0, -0.3, 0.30),
                       frame((T.TX1 - 30.0, 50.0, -40.0), 320.0, 0.30, 0.30)])


def sec8(m, root):
    site(m, root)
    T.loop(m, root, B3)
    T.plume(m, root, B3)
    T.tags(root, [
        [("SPX Technologies (SPXC): Marley", T.TOWER_TAG), ("EVAPCO (private)", T.FILL_TAG)],
        [("Baltimore Aircoil (Amsted, private)", T.TOWER_TAG), ("Johnson Controls (JCI), Trane (TT)", T.PLANT_TAG)],
        [("Modine (MOD): dry coolers", T.FAN_TAG), ("Vertiv (VRT): plant to rack", T.PLANT_TAG)],
    ])
    camera_path(root, [T.SITE, frame((FANC[0], 200.0, -60.0), 420.0, -0.25, 0.30), T.SITE])


def sec9(m, root):
    s = site(m, root)
    T.loop(m, root, [0])
    T.plume(m, root, [0, 1], n=14, h=260.0)
    T.makeup(m, root, s, [1])
    d = T.N.dry_bench(m, root)
    T.N.dry_flow(m, root, d, [2])
    show(d["hot"], T.span(2, 0.0, 3, 0.0))
    T.tags(root, [
        [("HEAT OUT: every watt ends in the air", (FANC[0], DECK + 300.0, FANC[2])), ("wet: cheapest, uses water", T.SKY_TAG)],
        [("drought areas push back on water", T.METER_TAG), ("permits + local politics", T.TOWER_TAG)],
        [("dry coolers: no water, more power", d["top"]), ("warm-water liquid cooling helps", d["coil"])],
    ])
    camera_path(root, [frame((FANC[0], 300.0, -90.0), 620.0, 0.30, 0.20), frame((T.TX1, 80.0, -40.0), 360.0, 0.30, 0.30),
                       frame((0.0, BY + 80.0, T.N.DB[2]), 440.0, 0.35, 0.30)])


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}


def build(n):
    m, root = T.setup(f"section_{n}", BEATS)
    SECTIONS[n](m, root)
    T.N.finish(f"section_{n}", page=T.PAGE)


if __name__ == "__main__":
    build(int(sys.argv[sys.argv.index("--") + 1]))
