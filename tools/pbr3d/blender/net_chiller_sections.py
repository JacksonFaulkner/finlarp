"""The CHILLER page's nine numbered sections. Section N illustrates heading N of
tui/src/screens/diagrams_pages/NET_CHILLER.txt (the tenth, Sources, is text only). Three beats each.

    blender -b --factory-startup --python tools/pbr3d/blender/net_chiller_sections.py -- <n>

  1 what happens   water out to the hall; refrigerant pumps the heat uphill; heat dumped outdoors
  2 the parts      the four-part loop drawn big: evaporator, compressor, condenser, valve
  3 in order       the loop one leg at a time
  4 how much heat  tons and kW; a 1-2 MW unit; a 100 MW campus needs dozens
  5 compressors    screw rotors; centrifugal impeller; magnetic bearings
  6 COP + temps    COP by machine; warmer water, less lift; free cooling
  7 dry coolers    free-cooling coil; a dry cooler; adiabatic assist
  8 who makes it   makers tagged on the site
  9 chokepoints    refrigerant rules; heat-wave peak; lead times
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net_chiller_detail as N  # noqa: E402
from net_chiller_detail import F, show, frame, camera_path, run, blink, CH, BY  # noqa: E402

BEATS = 3
B3 = [0, 1, 2]
Z = N.CB[2]


def site(m, root, leds=True):
    s = N.scene(m, root)
    if leds:
        for k in range(BEATS):
            blink(s["leds"], k, [0, 2, 4, 6], n=8, on=0.7)
    return s


def sec1(m, root):
    s = site(m, root)
    N.water(m, root, s, B3)
    N.boil(m, root, [1])
    N.refrigerant(m, root, s, [1])
    N.comp_heat(m, root, [1])
    N.fans_spin(s, B3)
    show(s["p"]["hot"], N.span(2, 0.0, 3, 0.0))
    N.plumes(m, root, [2])
    N.tags(root, [
        [("chilled water to the hall", (-20.0, 12.0, -150.0)), ("warm water back", (-20.0, 24.0, -120.0)), ("air handler coil", N.AHU_TAG)],
        [("evaporator takes the heat", N.EVAP_TAG), ("compressor lifts it", N.COMP_TAG), ("valve resets the loop", N.VALVE_TAG)],
        [("condenser + fans", N.FAN_TAG), ("heat out to the air", (CH.CX0 + 186.0, CH.CY1 + 70.0, -60.0))],
    ])
    camera_path(root, [N.SITE, N.UNIT, frame((180.0, 110.0, -60.0), 360.0, 0.30, 0.50)])


def sec2(m, root):
    c = N.cycle_bench(m, root)
    N.cycle_water(m, root, c, B3)
    N.cycle_flow(m, root, c, B3)
    N.cycle_boil(m, root, B3)
    N.cycle_drip(m, root, B3)
    N.tags(root, [
        [("EVAPORATOR", c["ev"]), ("CONDENSER", c["cd"])],
        [("COMPRESSOR", c["cmp"]), ("EXPANSION VALVE", c["xv"])],
        [("REFRIGERANT: R-134a, R-1234ze, R-513A", (0.0, BY, Z)), ("CHILLED WATER", (N.SHX[1] + 50.0, N.EVY + 8.0, Z))],
    ])
    camera_path(root, [frame((0.0, BY, Z), 380.0, 0.15, 0.15), frame((0.0, BY, Z), 460.0, -0.20, 0.15),
                       frame((0.0, BY, Z), 470.0, 0.25, 0.25)])


def sec3(m, root):
    c = N.cycle_bench(m, root)
    N.cycle_water(m, root, c, [0])
    N.cycle_boil(m, root, [0])
    N.cycle_flow(m, root, c, [0], ("suc",), u0=0.4)
    N.cycle_flow(m, root, c, [1], ("dis",))
    N.cycle_drip(m, root, [1])
    N.cycle_flow(m, root, c, [2], ("liq", "flash"))
    N.tags(root, [
        [("1 water warms the refrigerant: it boils", c["ev"]), ("2 vapour to the compressor", (N.CPX, N.EVY + 14.0, Z))],
        [("3 squeezed hot", c["cmp"]), ("4 condenses, heat out", c["cd"])],
        [("5 valve: pressure drops", c["xv"]), ("6 cold mix back in", (N.XVX, N.EVY - 14.0, Z))],
    ])
    camera_path(root, [frame((40.0, N.EVY + 20.0, Z), 330.0, 0.15, 0.15), frame((60.0, CH.CY1 + BY - 40.0, Z), 330.0, -0.10, 0.20),
                       frame((-90.0, BY, Z), 320.0, 0.20, 0.15)])


def sec4(m, root):
    g1, t1 = N.bars(m, root, "b1", -120.0, BY, Z, [(35.0, "bar_b", ""), (100.0, "bar_a", ""), (200.0, "bar_r", "")], w=50.0, gap=30.0, unit=1.0)
    s = site(m, root, leds=False)
    N.water(m, root, s, [2])
    N.fans_spin(s, [2])
    N.present(g1, N.span(0, 0.0, 2, 0.0))
    N.tags(root, [
        [("1 ton = 3.5 kW of cooling", t1[0]), ("1 MW = ~285 tons", t1[1]), ("big units: 1-2 MW (300-600 tons)", t1[2])],
        [("one 130 kW GB200 rack = ~37 tons", t1[0]), ("100 MW campus: 50-100 chillers", t1[2])],
        [("one unit", (180.0, CH.CY1 + 30.0, -60.0)), ("hall heat in", N.HALL_TAG)],
    ])
    camera_path(root, [frame((-20.0, BY + 90.0, Z), 330.0, 0.15, 0.15), frame((-20.0, BY + 90.0, Z), 330.0, -0.15, 0.20), N.SITE])


def sec5(m, root):
    sc = N.screw_bench(m, root)
    N.screw_gas(m, root, [0])
    N.present(sc["g"], N.span(0, 0.0, 1, 0.0))
    c = (0.0, BY + 400.0, -60.0)
    cen = N.centri_bench(m, root, c=c)
    N.C.spin(cen["imp"], [1, 2], turns=6.0, axis=2)
    N.centri_gas(m, root, c, [1])
    show(cen["brg"], N.span(0, 0.0, 1, 0.0) + N.span(2, 0.0, 3, 0.0))
    N.tags(root, [
        [("SCREW: two meshing rotors", sc["rot"]), ("mid-size, air-cooled units", sc["mot"])],
        [("CENTRIFUGAL: an impeller flings gas out", cen["eye"]), ("the big water-cooled units", cen["dis"])],
        [("MAGNETIC BEARINGS: shaft floats", cen["mb"]), ("oil-free, ~0.5 kW/ton", cen["mot"])],
    ])
    camera_path(root, [frame((0.0, BY + 10.0, -60.0), 360.0, 0.30, 0.45), frame((20.0, BY + 400.0, -60.0), 260.0, 0.25, 0.20),
                       frame((0.0, BY + 400.0, -110.0), 260.0, 1.0, 0.20)])


def sec6(m, root):
    g1, t1 = N.bars(m, root, "cop", -150.0, BY, Z, [(30.0, "bar_r", ""), (65.0, "bar_a", ""), (90.0, "bar_b", ""), (180.0, "bar_g", "")],
                    w=44.0, gap=26.0, unit=1.0)
    g2, t2 = N.bars(m, root, "lift", -100.0, BY + 400.0, Z, [(120.0, "bar_r", ""), (60.0, "bar_b", "")], w=60.0, gap=60.0, unit=1.0)
    N.tags(root, [
        [("air-cooled: COP ~3", t1[0]), ("water-cooled: ~6-7", t1[1]), ("warm water: ~9", t1[2]), ("free cooling: 15+", t1[3])],
        [("7 C water: big lift", t2[0]), ("18 C water: half the lift", t2[1])],
        [("COP = heat moved / power in", t1[3]), ("each 1 C warmer: ~2-3% less power", t1[1])],
    ])
    camera_path(root, [frame((-20.0, BY + 70.0, Z), 330.0, 0.15, 0.15), frame((-10.0, BY + 460.0, Z), 280.0, 0.10, 0.15),
                       frame((-20.0, BY + 70.0, Z), 340.0, -0.25, 0.20)])


def sec7(m, root):
    s = site(m, root, leds=False)
    N.water(m, root, s, [0])
    N.fans_spin(s, [0])
    show(s["p"]["free"], N.span(0, 0.1, 1, 0.0))
    run(root, "w_free", N.FREE, 9, 4.0, m["c_supply"], [0], 0.1, 0.8, 50)
    d = N.dry_bench(m, root)
    N.dry_flow(m, root, d, [1])
    N.dry_flow(m, root, d, [2], adiabatic=True, name="dfa")
    show(d["hot"], N.span(1, 0.0, 3, 0.0))
    N.tags(root, [
        [("FREE COOLING: coil before the compressor", N.FREE_TAG), ("compressor off", N.COMP_TAG)],
        [("DRY COOLER: coil + fans only", d["top"]), ("good for 30-45 C liquid loops", d["coil"])],
        [("ADIABATIC: wet pads on hot days", d["pad"]), ("water only a few hundred hours a year", (0.0, BY + 40.0, N.DB[2] + 160.0))],
    ])
    camera_path(root, [frame((180.0, 85.0, -80.0), 330.0, 0.45, 0.40), frame((0.0, BY + 80.0, N.DB[2]), 440.0, 0.35, 0.30),
                       frame((0.0, BY + 80.0, N.DB[2]), 440.0, -0.55, 0.25)])


def sec8(m, root):
    s = site(m, root)
    N.water(m, root, s, B3)
    N.fans_spin(s, B3)
    N.tags(root, [
        [("Trane (TT), Carrier (CARR)", (180.0, CH.CY1 + 30.0, -60.0)), ("Johnson Controls / York (JCI)", N.COMP_TAG)],
        [("Daikin, Mitsubishi, LG", (180.0, CH.CY1 + 30.0, -60.0)), ("Modine / Airedale (MOD)", N.FAN_TAG)],
        [("Vertiv (VRT): chillers to CDUs", N.AHU_TAG), ("Danfoss: Turbocor compressors", N.COMP_TAG)],
    ])
    camera_path(root, [N.UNIT, frame((180.0, 110.0, -60.0), 360.0, 0.35, 0.50), N.SITE])


def sec9(m, root):
    c = N.cycle_bench(m, root)
    N.cycle_flow(m, root, c, [0])
    s = site(m, root, leds=False)
    N.water(m, root, s, [1])
    N.refrigerant(m, root, s, [1])
    N.comp_heat(m, root, [1])
    N.fans_spin(s, [1, 2], turns=5.0)
    show(s["p"]["hot"], N.span(1, 0.0, 3, 0.0))
    N.plumes(m, root, [1, 2], n=10, h=110.0)
    N.tags(root, [
        [("HFC phase-down: GWP limit 700", c["cd"]), ("new low-GWP refrigerants", c["ev"])],
        [("heat wave: least capacity at peak load", N.FAN_TAG), ("compressor at full power", N.COMP_TAG)],
        [("big chillers: long lead times", (180.0, CH.CY1 + 30.0, -60.0)), ("factories expanding", (CH.CX1, 60.0, 0.0))],
    ])
    camera_path(root, [frame((0.0, BY, Z), 420.0, 0.15, 0.15), frame((180.0, 110.0, -60.0), 360.0, 0.30, 0.50),
                       frame((150.0, 80.0, -60.0), 420.0, -0.25, 0.35)])


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}


def build(n):
    m, root = N.setup(f"section_{n}", BEATS)
    SECTIONS[n](m, root)
    N.finish(f"section_{n}", page=N.PAGE)


if __name__ == "__main__":
    build(int(sys.argv[sys.argv.index("--") + 1]))
