"""TRM_EMS: the Terms-tab overview for EMS (electronics manufacturing services, contract manufacturing).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_ems.py

A factory floor seen from above: on the left the brand owner's design arrives as a drawing; parts crates
come in from suppliers; bare boards run down a conveyor through a solder-paste printer, a pick-and-place
machine and a reflow oven, then a test bay, then into server racks that leave on a truck. A margin pair
(revenue vs the EMS slice) closes it out.

Beats:
  0 design    the brand owner designs; the EMS firm builds
  1 smt       parts in, boards through paste, pick-and-place, reflow
  2 test      test bay, boards into servers and racks
  3 ship      racks out to the customer from plants in several countries
  4 margin    big revenue, thin slice: how to read EMS
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import F, bx, empty, mat  # noqa: E402
from power_vrm_detail import frame, run, rise, present  # noqa: E402
import kit_ledger as K  # noqa: E402
import kit_supply as S  # noqa: E402

SLUG = "TRM_EMS"
BEATS = [
    ("EMS firms build hardware that other companies design",
     "Brand owners like cloud providers and GPU vendors design boards and servers but do not run their own factories. "
     "An electronics manufacturing services firm takes the design files and builds the product under contract."),
    ("Parts come in, boards go through the surface-mount line",
     "The EMS firm buys the components on the bill of materials. A printer lays solder paste, pick-and-place machines "
     "set thousands of parts a minute, and a reflow oven melts the solder to fix them to the board."),
    ("Every board is tested, then built into servers and racks",
     "Boards go through electrical and functional test, then get built into servers. For AI, whole racks are cabled, "
     "filled with liquid-cooling plumbing and burned in at the plant before they ship."),
    ("Plants in several countries ship finished racks",
     "Large EMS firms run plants in Mexico, Taiwan, China, Southeast Asia and elsewhere, so they can move builds closer "
     "to customers or around tariffs. How fast they build racks sets how fast GPU capacity comes online."),
    ("Huge revenue, thin margin: watch the slice the assembly step keeps",
     "Pass-through parts like GPUs inflate EMS revenue, but the build step keeps only a few percent as operating margin. "
     "Rack-scale integration earns more than plain board assembly. Related: Foxconn (2317.TW), Jabil (JBL), Flex (FLEX), "
     "Celestica (CLS), Sanmina (SANM)."),
]

LINE_Z = 0.0
STATIONS = [(-120.0, "printer"), (-60.0, "pnp"), (10.0, "oven"), (80.0, "test")]


def mats(m):
    m["em_floor"] = mat("em_floor", (0.16, 0.17, 0.19), rough=0.8)
    m["em_belt"] = mat("em_belt", (0.08, 0.08, 0.09), rough=0.7)
    m["em_mach"] = mat("em_mach", (0.78, 0.80, 0.82), metal=0.3, rough=0.4)
    m["em_rack"] = mat("em_rack", (0.10, 0.11, 0.13), metal=0.6, rough=0.4)
    m["em_ok"] = mat("em_ok", (0.30, 0.95, 0.45), emit=(0.30, 0.95, 0.45), strength=4.0)
    m["em_oven"] = mat("em_oven", (1.0, 0.45, 0.15), emit=(1.0, 0.45, 0.15), strength=3.0)
    m["em_rev"] = mat("em_rev", (0.70, 0.72, 0.76), rough=0.6)
    m["em_slice"] = mat("em_slice", (0.25, 0.60, 0.40), rough=0.6)
    m["em_truck"] = mat("em_truck", (0.85, 0.85, 0.82), rough=0.5)


def line(m, root):
    bx("belt", (-160.0, 6.0, LINE_Z - 8.0), (120.0, 8.0, LINE_Z + 8.0), m["em_belt"], root)
    for k in range(15):
        x = -158.0 + k * 20.0
        bx(f"leg{k}", (x, 0.0, LINE_Z - 8.0), (x + 2.0, 6.0, LINE_Z - 6.0), m["steel"], root)
        bx(f"legb{k}", (x, 0.0, LINE_Z + 6.0), (x + 2.0, 6.0, LINE_Z + 8.0), m["steel"], root)
    # printer: low box with a squeegee bar
    bx("printer", (-136.0, 8.0, -14.0), (-104.0, 22.0, 14.0), m["em_mach"], root)
    bx("squeegee", (-130.0, 22.0, -10.0), (-128.0, 26.0, 10.0), m["steel"], root)
    # pick-and-place: gantry with a head that wiggles
    S.chamber(m, root, "pnp", (-60.0, 8.0, 0.0), 40.0, 26.0, 30.0)
    head = bx("pnp_head", (-4.0, 0.0, -4.0), (4.0, 8.0, 4.0), m["mold"], root)
    head.location = (-60.0, 22.0, 0.0)
    C.wiggle(head, [1], amp=(10.0, 0.0, 6.0), period=4)
    # reflow oven: long box with glowing windows
    bx("oven", (-15.0, 8.0, -14.0), (35.0, 30.0, 14.0), m["em_mach"], root)
    for k in range(4):
        bx(f"ovw{k}", (-11.0 + k * 12.0, 14.0, 14.0), (-3.0 + k * 12.0, 22.0, 14.6), m["em_oven"], root)
    rise(root, "ovheat", (10.0, 31.0, 0.0), 8, 1.4, m["em_oven"], 1, h=24.0, spread=(20.0, 6.0))
    # test bay: frame with a status lamp
    bx("test", (68.0, 8.0, -14.0), (92.0, 34.0, -10.0), m["em_mach"], root)
    bx("test_top", (68.0, 34.0, -14.0), (92.0, 36.0, 14.0), m["em_mach"], root)
    lamp = empty("lamp", root)
    bx("lamp_b", (77.0, 36.0, -2.0), (83.0, 40.0, 4.0), m["em_ok"], lamp)
    present(lamp, [(F(2, 0.2), F(5, 0))])


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.ldg_materials(m)
    S.materials(m)
    mats(m)
    bx("floor", (-260.0, -4.0, -180.0), (260.0, -2.0, 120.0), m["em_floor"], root)
    line(m, root)

    # brand owner's design: a drawing sheet at far left, data beads into the factory
    K.ledger_sheet(m, root, "design", (-215.0, 0.0, -60.0), 50.0, 60.0, lines=6)
    run(root, "files", [(-215.0, 40.0, -55.0), (-150.0, 20.0, -20.0)], 6, 2.0, m["ldg_blue_b"], [0, 1], 0.1, 0.8, 30)
    # parts crates from suppliers feed the line
    K.order_stack(m, root, "parts", (-160.0, 0.0, 50.0), 3, 2, s=8.0)
    run(root, "feed", [(-160.0, 20.0, 50.0), (-140.0, 12.0, 0.0)], 5, 2.0, m["ldg_gold_b"], 1, 0.0, 0.6, 30)
    # boards riding the belt
    run(root, "boards", [(-155.0, 10.0, 0.0), (115.0, 10.0, 0.0)], 10, 3.0, m["em_ok"], [1, 2], 0.0, 0.9, 60)

    # servers and racks after test
    racks = empty("racks", root)
    for k in range(3):
        x = 140.0 + k * 24.0
        bx(f"rack{k}", (x, 0.0, -20.0), (x + 18.0, 60.0, -4.0), m["em_rack"], racks)
        for s in range(8):
            bx(f"srv{k}_{s}", (x + 1.0, 4.0 + s * 7.0, -4.0), (x + 17.0, 9.0 + s * 7.0, -3.4), m["em_mach"], racks)
            bx(f"led{k}_{s}", (x + 14.0, 6.0 + s * 7.0, -3.4), (x + 16.0, 7.0 + s * 7.0, -3.0), m["em_ok"], racks)
    present(racks, [(F(2, 0.3), F(5, 0))])

    # truck and flags for plants in several countries
    truck = empty("truck", root)
    bx("trk_box", (150.0, 2.0, 40.0), (220.0, 34.0, 64.0), m["em_truck"], truck)
    bx("trk_cab", (220.0, 2.0, 42.0), (238.0, 24.0, 62.0), m["car"], truck)
    for k, wx in enumerate((160.0, 205.0, 230.0)):
        bx(f"whl{k}", (wx - 5.0, -2.0, 38.0), (wx + 5.0, 6.0, 66.0), m["rubber"], truck)
    present(truck, [(F(3, 0), F(5, 0))])
    run(root, "ship", [(170.0, 30.0, -10.0), (185.0, 40.0, 50.0)], 6, 2.4, m["ldg_blue_b"], 3, 0.0, 0.7, 30)
    plants = empty("plants", root)
    for k, (px, pz) in enumerate(((-230.0, 100.0), (-120.0, 100.0), (0.0, 100.0), (120.0, 100.0))):
        bx(f"plant{k}", (px, 0.0, pz - 10.0), (px + 50.0, 22.0, pz + 10.0), m["em_mach"], plants)
        bx(f"roof{k}", (px, 22.0, pz - 10.0), (px + 50.0, 24.0, pz + 10.0), m["em_rack"], plants)
    present(plants, [(F(3, 0), F(5, 0))])

    # margin pair
    marg = empty("marg", root)
    present(marg, [(F(4, 0), F(5, 0))])
    rev = K.ledger_bar(m, marg, "rev", -200.0, -140.0, 22.0, {4: 100.0}, "em_rev")
    slc = K.ledger_bar(m, marg, "slice", -170.0, -140.0, 22.0, {4: 6.0}, "em_slice")
    K.coin_stack(m, marg, "fee", (-170.0, 7.0, -140.0), 3, r=6.0, h=1.6)

    C.tags(root, {
        0: [("brand owner designs", (-215.0, 70.0, -60.0)), ("EMS firm builds", (-60.0, 45.0, 0.0))],
        1: [("solder paste", (-120.0, 30.0, 0.0)), ("pick-and-place", (-60.0, 40.0, 0.0)),
            ("reflow oven", (10.0, 40.0, 0.0)), ("parts from BOM", (-160.0, 25.0, 50.0))],
        2: [("every board tested", (80.0, 45.0, 0.0)), ("racks burned in at plant", (165.0, 65.0, -12.0))],
        3: [("racks ship to customer", (190.0, 40.0, 50.0)), ("plants in many countries", (-60.0, 30.0, 100.0))],
        4: [("revenue includes the GPUs", (-200.0, 105.0, -140.0)), ("assembly keeps a few %", (-170.0, 20.0, -140.0)),
            ("2317.TW JBL FLEX CLS SANM", (-185.0, 70.0, -110.0))],
    })
    C.done(SLUG, BEATS, [
        frame((-140.0, 20.0, -20.0), 200.0, 0.25, 0.45),
        frame((-60.0, 15.0, 10.0), 230.0, 0.10, 0.55),
        frame((130.0, 25.0, -5.0), 170.0, -0.20, 0.40),
        frame((60.0, 20.0, 50.0), 400.0, -0.10, 0.50, pad=1.0),
        frame((-185.0, 45.0, -130.0), 260.0, 0.20, 0.30, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
