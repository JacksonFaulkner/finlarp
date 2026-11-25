"""Zoom-ins (a-e) for the CHILLER page, three beats each (diagrams_nodes/netcool/chiller/zooms.rs):

  a evaporator      the cycle bench: warm water in the tubes, refrigerant boiling round them
  b compressor      a twin-screw compressor cut open, then a centrifugal one on magnetic bearings
  c condenser       hot gas in the V-bank coils, fans pulling air, heat leaving the deck
  d free cooling    compressor running, then off with the free-cooling coil lit
  e dry cooler      a dry cooler: no compressor; adiabatic pads on a hot day

    blender -b --factory-startup --python tools/pbr3d/blender/net_chiller_zooms.py -- a

Writes assets/net_chiller_zoom_<letter>.glb.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net_chiller_detail as N  # noqa: E402
from net_chiller_detail import F, show, frame, camera_path, run, blink, CH, BY  # noqa: E402

BEATS = 3
B3 = [0, 1, 2]


def zoom_a(m, root):
    c = N.cycle_bench(m, root)
    N.cycle_water(m, root, c, B3)
    N.cycle_boil(m, root, [1, 2])
    N.cycle_flow(m, root, c, [2], ("flash", "suc"))
    z = N.CB[2]
    N.tags(root, [
        [("warm water in ~25-30 C", (N.SHX[0] - 50.0, N.EVY + 8.0, z)), ("copper tube bundle", (-40.0, N.EVY + 14.0, z + 4.0)),
         ("colder water out", (N.SHX[1] + 50.0, N.EVY + 8.0, z))],
        [("refrigerant boils on the tubes", (0.0, N.EVY - 18.0, z + 8.0)), ("low pressure: boils cold", c["ev"])],
        [("cold liquid in", (N.XVX, N.EVY - 14.0, z)), ("vapour to the compressor", (N.CPX, N.EVY + 14.0, z))],
    ])
    camera_path(root, [frame((0.0, N.EVY, z), 300.0, 0.15, 0.20), frame((0.0, N.EVY, z), 200.0, 0.0, 0.10),
                       frame((0.0, N.EVY + 20.0, z), 420.0, 0.20, 0.25)])


def zoom_b(m, root):
    sc = N.screw_bench(m, root)
    N.screw_gas(m, root, [0, 1])
    N.present(sc["g"], N.span(0, 0.0, 2, 0.0))
    c = (0.0, BY + 400.0, -60.0)
    cen = N.centri_bench(m, root, c=c)
    N.C.spin(cen["imp"], [2], turns=6.0, axis=2)
    N.centri_gas(m, root, c, [2])
    N.tags(root, [
        [("suction: cold vapour", sc["in"]), ("male + female rotors", sc["rot"]), ("motor", sc["mot"])],
        [("pockets shrink along the screws", (0.0, BY + 40.0, -60.0)), ("hot dense gas out", sc["out"])],
        [("centrifugal impeller", cen["eye"]), ("magnetic bearings: no oil", cen["mb"]), ("to the condenser", cen["dis"])],
    ])
    camera_path(root, [frame((0.0, BY + 10.0, -60.0), 360.0, 0.30, 0.45), frame((40.0, BY, -60.0), 300.0, -0.1, 0.55),
                       frame((20.0, BY + 400.0, -60.0), 260.0, 0.35, 0.25)])


def zoom_c(m, root):
    s = N.scene(m, root)
    N.refrigerant(m, root, s, B3, ("dis",))
    show(s["p"]["hot"], N.span(0, 0.3, 3, 0.0))
    N.fans_spin(s, B3, turns=4.0)
    N.plumes(m, root, [1, 2])
    N.tags(root, [
        [("hot gas into the coils", (CH.CMP[1] - 30.0, 70.0, -60.0)), ("V-bank condenser coils", N.COND_TAG)],
        [("fans pull outside air through", N.FAN_TAG), ("air leaves ~10-15 C warmer", (CH.CX0 + 186.0, CH.CY1 + 70.0, -60.0))],
        [("gas condenses to liquid", (CH.CX0 + 20.0, 70.0, -60.0)), ("heat out = IT heat + compressor", (CH.CX0 + 113.0, CH.CY1 + 90.0, -60.0))],
    ])
    camera_path(root, [frame((180.0, 85.0, -40.0), 300.0, 0.15, 0.15),
                       [(0.0, frame((180.0, 120.0, -60.0), 330.0, 0.30, 0.60)), (0.55, frame((180.0, 150.0, -60.0), 330.0, -0.2, 0.7))],
                       frame((150.0, 100.0, -60.0), 380.0, 0.35, 0.40)])


def zoom_d(m, root):
    s = N.scene(m, root)
    N.water(m, root, s, B3)
    N.refrigerant(m, root, s, [0])
    N.comp_heat(m, root, [0])
    N.fans_spin(s, B3)
    show(s["p"]["free"], N.span(1, 0.1, 3, 0.0))
    run(root, "w_free", N.FREE, 9, 4.0, m["c_supply"], [1, 2], 0.1, 0.8, 50)
    N.tags(root, [
        [("hot day: compressor runs", N.COMP_TAG), ("all heat through the refrigerant", N.EVAP_TAG)],
        [("cold day: free-cooling coil", N.FREE_TAG), ("compressor off", N.COMP_TAG)],
        [("warm water (30 C+): free most hours", N.FAN_TAG), ("energy falls 50-80%", (CH.CX1, 60.0, 0.0))],
    ])
    camera_path(root, [N.UNIT, frame((180.0, 85.0, -80.0), 330.0, 0.45, 0.40), frame((180.0, 85.0, -70.0), 380.0, -0.3, 0.35)])


def zoom_e(m, root):
    d = N.dry_bench(m, root)
    N.dry_flow(m, root, d, [0, 1])
    N.dry_flow(m, root, d, [2], adiabatic=True, name="dfa")
    show(d["hot"], N.span(0, 0.2, 3, 0.0))
    N.tags(root, [
        [("warm water in", d["sup"][0]), ("finned coils, V-bank", d["coil"]), ("no compressor", d["top"])],
        [("fans pull air through", d["top"]), ("water can only reach ~5 C above air", d["coil"])],
        [("adiabatic pads: wetted on hot days", d["pad"]), ("evaporation pre-cools the air", (0.0, BY + 40.0, N.DB[2] + 160.0))],
    ])
    camera_path(root, [frame((0.0, BY + 80.0, N.DB[2]), 440.0, 0.35, 0.30), frame((0.0, BY + 120.0, N.DB[2]), 440.0, 0.20, 0.55),
                       frame((0.0, BY + 80.0, N.DB[2]), 440.0, 0.60, 0.25)])


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}


def run_zoom(letter):
    name = f"zoom_{letter}"
    m, root = N.setup(name, BEATS)
    ZOOMS[letter](m, root)
    N.finish(name, page=N.PAGE)


if __name__ == "__main__":
    run_zoom(sys.argv[sys.argv.index("--") + 1])
