"""Zoom-ins (a-e) for the COOLING TOWER page, three beats each (diagrams_nodes/netcool/cooling_tower/zooms.rs):

  a fill          four fill sheets close up: films running down, air rising, vapour leaving
  b evaporation   one drop: vapour leaves its skin and carries heat; the rest cools
  c drift         chevron blades: vapour weaves through, droplets are caught
  d water use     make-up meter, blowdown, litres per day
  e heat out      wet tower plume vs a dry cooler: two ways into the air

    blender -b --factory-startup --python tools/pbr3d/blender/net_cooling_tower_zooms.py -- a
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net_cooling_tower_detail as T  # noqa: E402
from net_cooling_tower_detail import show, frame, camera_path, blink, C, FANC, DECK, BY  # noqa: E402

BEATS = 3
B3 = [0, 1, 2]


def zoom_a(m, root):
    f = T.fill_bench(m, root)
    show(f["film"], T.span(0, 0.1, 3, 0.0))
    T.fill_flow(m, root, B3)
    T.tags(root, [
        [("warm water from the nozzles", f["top"]), ("corrugated PVC fill", f["sheet"])],
        [("water spreads into thin films", f["sheet"]), ("air rises between sheets", f["gap"])],
        [("vapour leaves the film surface", (40.0, BY + 60.0, T.FB[2])), ("cooled water drips out", f["bottom"])],
    ])
    camera_path(root, [frame((0.0, BY + 60.0, T.FB[2]), 250.0, 0.30, 0.20), frame((-40.0, BY, T.FB[2]), 200.0, 0.10, 0.10),
                       frame((0.0, BY - 20.0, T.FB[2]), 300.0, -0.25, 0.15)])


def zoom_b(m, root):
    d = T.drop_bench(m, root, B3)
    g, t = T.bars(m, root, "lh", 200.0, T.DRP[1] - 100.0, T.DRP[2], [(140.0, "bar_r", ""), (25.0, "bar_a", "")], w=40.0, gap=30.0)
    T.present(g, T.span(1, 0.0, 3, 0.0))
    T.tags(root, [
        [("warm drop ~35 C", d["drop"]), ("vapour off its skin", d["vap"])],
        [("evaporating 1 kg: ~2,400 kJ", t[0]), ("warming 1 kg by 6 C: ~25 kJ", t[1])],
        [("so ~1% evaporating cools the rest ~6 C", d["below"]), ("limit: wet-bulb temperature", d["vap"])],
    ])
    camera_path(root, [frame((0.0, T.DRP[1], T.DRP[2]), 300.0, 0.20, 0.15), frame((140.0, T.DRP[1], T.DRP[2]), 420.0, 0.15, 0.15),
                       frame((60.0, T.DRP[1], T.DRP[2]), 380.0, -0.2, 0.15)])


def zoom_c(m, root):
    d = T.drift_bench(m, root)
    T.drift_flow(m, root, B3)
    T.tags(root, [
        [("chevron blades", d["blade"]), ("air + droplets from the spray", d["below"])],
        [("droplets can't turn: they hit and drain", (40.0, T.DRB[1] - 20.0, T.DRB[2])), ("vapour weaves through", d["above"])],
        [("drift: ~0.001% of flow or less", d["above"]), ("less water lost, fewer aerosols", d["blade"])],
    ])
    camera_path(root, [frame((0.0, T.DRB[1], T.DRB[2]), 300.0, 0.20, 0.15), frame((20.0, T.DRB[1], T.DRB[2]), 220.0, 0.05, 0.10),
                       frame((0.0, T.DRB[1] + 20.0, T.DRB[2]), 320.0, -0.25, 0.20)])


def zoom_d(m, root):
    s = T.scene(m, root)
    T.loop(m, root, B3)
    C.spin(s["fan"], B3, turns=4.0)
    T.plume(m, root, B3)
    T.makeup(m, root, s, [0, 1])
    g, t = T.bars(m, root, "lpd", -100.0, BY, -40.0, [(36.0, "bar_b", ""), (60.0, "bar_a", ""), (120.0, "bar_r", "")], w=50.0, gap=30.0)
    T.tags(root, [
        [("make-up water meter", T.METER_TAG), ("replaces what evaporates", T.SKY_TAG)],
        [("blowdown: bleeds off minerals", T.BD_TAG), ("3-6 cycles of concentration", T.BASIN_TAG)],
        [("100 MW of heat: ~3.6M L/day", t[2]), ("~1.5 L per kWh evaporated", t[0]), ("+ blowdown", t[1])],
    ])
    camera_path(root, [frame((T.TX1 + 20.0, 50.0, -40.0), 240.0, 0.30, 0.30), frame((T.TX0 - 10.0, 40.0, -20.0), 220.0, -0.3, 0.30),
                       frame((0.0, BY + 70.0, -40.0), 300.0, 0.15, 0.15)])


def zoom_e(m, root):
    s = T.scene(m, root)
    T.loop(m, root, [0])
    C.spin(s["fan"], [0, 1], turns=4.0)
    T.plume(m, root, [0, 1], n=14, h=240.0)
    d = T.N.dry_bench(m, root)
    T.N.dry_flow(m, root, d, [1, 2])
    show(d["hot"], T.span(1, 0.0, 3, 0.0))
    T.tags(root, [
        [("WET: heat leaves as vapour", T.SKY_TAG), ("water can approach wet-bulb", T.BASIN_TAG)],
        [("both end up in the outdoor air", (FANC[0], DECK + 300.0, FANC[2])), ("DRY: hot air, no water", d["top"])],
        [("dry: warmer water, more fan power", d["coil"]), ("zero evaporation", d["top"])],
    ])
    camera_path(root, [frame((FANC[0], 250.0, -90.0), 480.0, 0.25, 0.25), frame((FANC[0], 300.0, -90.0), 620.0, 0.30, 0.20),
                       frame((0.0, BY + 80.0, T.N.DB[2]), 440.0, 0.35, 0.30)])


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}


def run_zoom(letter):
    name = f"zoom_{letter}"
    m, root = T.setup(name, BEATS)
    ZOOMS[letter](m, root)
    T.N.finish(name, page=T.PAGE)


if __name__ == "__main__":
    run_zoom(sys.argv[sys.argv.index("--") + 1])
