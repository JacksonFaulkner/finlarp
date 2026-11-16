"""The SWITCHGEAR node page's overview, in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/power_switchgear_overview.py

Writes blender/power_switchgear_overview.blend and assets/power_switchgear_overview.glb. One beat is 8 s.

The scene is a data-center power campus built at 1 unit = 1 cm (root scaled x2 at the end), seen from
above the front: two utility transformers at the back fed from an H-frame line end, two standby
generators between them, the switchgear house (two mirror-image metal-clad lineups, A and B, each
utility main + four feeders + generator breaker under an open bus duct), the unit substations, and
the data hall with its UPS and A and B busways over three rack rows. Parts come from
power_switchgear_detail.py. Beads ride the lines, cables and bus bars: amber = medium voltage from
the utility, green = generator power, cyan = 480 V, red = fault current.

Beats (match the seven beats in diagrams_nodes/power/switchgear/overview.rs):
  0 yard       utility power down the line, through the transformers, along MV cables into the house
  1 feeds      the bus splits it into feeder breakers; a feeder runs to each unit substation, 480 V to the hall
  2 fault      close on lineup A: a short on feeder 1; its relay trips its vacuum breaker; the rest stay on
  3 2N         paths A and B both feed the hall; A's main opens for service and B carries everything
  4 standby    the generators wait between the transformers; utility still feeds the house
  5 outage     the utility drops, generators start, the ATS opens the mains and closes the generator breakers
  6 back       the utility returns, the load transfers back and the generators run down

power_switchgear_zooms.py rebuilds this scene with its own camera and tags (it swaps LABEL and CAMERA).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
from pbr_kit import empty  # noqa: E402
import power_switchgear_detail as D  # noqa: E402
from power_switchgear_detail import frame, camera_path, beads, wire  # noqa: E402

PAGE = "power_switchgear"
NAME = "overview"
BEATS = 7
ROOT = 2.0

LABEL = label
CAMERA = camera_path
W = None  # the last build's campus points (cp), read by power_switchgear_zooms.py and _sections.py

# breaker timeline (frames)
FAULT = F(2, 0.18)
TRIP = F(2, 0.34)
SERVICE = F(3, 0.5)
LOST = F(5, 0.1)
GEN_ON = F(5, 0.5)
BACK = F(6, 0.1)
XFER_BACK = F(6, 0.35)


def utility_in(m, root, cp, side, b, u0=0.0, u1=0.8, end=None):
    """Amber beads down the three line conductors and the MV cable, in through the main breaker, onto the bus."""
    P = cp["paths"]
    for k, ln in enumerate(P[f"hv{side}"]):
        beads(root, f"hv{side}{b}_{k}", ln, m["mv"], b, u0, u1, size=6.0, speed=26.0, n=3, end=end)
    beads(root, f"mvc{side}{b}", P[f"mv{side}"], m["mv"], b, u0 + 0.05, u1, size=9.0, speed=30.0, n=4, end=end)
    L = cp[side]
    beads(root, f"main{side}{b}", D.through_cab(L["main"], 1, inward=True), m["mv"], b, u0 + 0.12, u1, size=4.0,
          speed=8.0, n=3, end=end)


def gen_in(m, root, cp, side, b, u0, u1, end=None):
    P = cp["paths"]
    beads(root, f"genc{side}{b}", P[f"gen{side}"], m["gen_e"], b, u0, u1, size=9.0, speed=30.0, n=4, end=end)
    beads(root, f"genb{side}{b}", D.through_cab(cp[side]["gen"], 1, inward=True), m["gen_e"], b, u0 + 0.08, u1,
          size=4.0, speed=8.0, n=3, end=end)


def distribute(m, root, cp, side, b, u0=0.0, u1=0.85, mt="mv", end=None, skip=(), hall=True, feeders=("f1", "f2", "f3", "f4")):
    """Along the bus, down each feeder breaker, out to the unit substation, 480 V to the UPS and the busways."""
    L = cp[side]
    bus = cp[f"bus{side}"]
    xs = [L["main"]["c"], L["gen"]["c"]]
    beads(root, f"bus{side}{b}", D.bus_path(bus, 1, xs[0], xs[1]), m[mt], b, u0, u1, size=5.0, speed=14.0, n=5, end=end)
    for kind in feeders:
        if kind in skip:
            continue
        beads(root, f"{kind}{side}{b}", D.through_cab(L[kind], 1), m[mt], b, u0 + 0.05, u1, size=4.0, speed=8.0, n=3, end=end)
    P = cp["paths"]
    if "f1" not in skip:
        beads(root, f"feed{side}{b}", P[f"feed{side}"], m[mt], b, u0 + 0.1, u1, size=8.0, speed=26.0, n=4, end=end)
        if hall:
            beads(root, f"lv{side}{b}", P[f"lv{side}"], m["lv"], b, u0 + 0.2, u1, size=10.0, speed=26.0, n=4, end=end)
            hl = cp["hall"]
            beads(root, f"head{side}{b}", hl["heads"][side] + [(hl["heads"][side][-1][0], hl["heads"][side][-1][1], D.ROWS[-1])],
                  m["lv"], b, u0 + 0.3, u1, size=8.0, speed=20.0, n=3, end=end)
            for r, row in enumerate(hl["rows"][side]):
                beads(root, f"row{side}{b}_{r}", row, m["lv"], b, u0 + 0.35 + 0.05 * r, u1, size=7.0, speed=20.0, n=2, end=end)


def build():
    global W
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = D.materials()
    cp = D.campus(m, root)
    W = cp
    A, B = cp["A"], cp["B"]
    end = F(BEATS, 0)

    # breakers
    D.breaker(A["main"], [(SERVICE, False), (F(4, 0), True), (LOST + 4, False), (XFER_BACK, True)], end=end)
    D.breaker(B["main"], [(LOST + 4, False), (XFER_BACK, True)], end=end)
    D.breaker(A["gen"], [(GEN_ON, True), (XFER_BACK - 6, False)], closed=False, end=end)
    D.breaker(B["gen"], [(GEN_ON, True), (XFER_BACK - 6, False)], closed=False, end=end)
    D.breaker(A["f1"], [(TRIP, False), (F(3, 0), True)], end=end)
    for side in ("A", "B"):
        for kind in ("f2", "f3", "f4"):
            D.breaker(cp[side][kind], [], end=end)
    for kind in ("f2", "f3", "f4"):
        pass
    D.breaker(B["f1"], [], end=end)
    show(A["f1"]["trip"], [(TRIP - 4, F(3, 0))])
    for side in ("A", "B"):
        for kind in ("main", "f2", "f3", "f4", "gen"):
            show(cp[side][kind]["trip"], [])
    show(B["f1"]["trip"], [])

    # utility lost: dark-red overlays on the lines and MV cables
    dead = empty("dead", root)
    for side in ("A", "B"):
        for k, ln in enumerate(cp["paths"][f"hv{side}"]):
            wire(f"dead_hv{side}{k}", ln, 2.6, m["dead"], dead, 6)
        wire(f"dead_mv{side}", cp["paths"][f"mv{side}"], 7.5, m["dead"], dead, 8)
    show(dead, [(LOST, BACK)])

    # generators run from the outage to the end of beat 6 (cool-down); alternators glow while loaded
    for side, G in (("A", cp["GA"]), ("B", cp["GB"])):
        show(G["glow"], [(F(5, 0.3), XFER_BACK)])
        D.exhaust(root, f"exh{side}5", G["stack"], m["smoke"], 5, 0.2, 0.95, n=8)
        D.exhaust(root, f"exh{side}6", G["stack"], m["smoke"], 6, 0.0, 0.7, n=5)

    # ---- flows per beat
    for side in ("A", "B"):
        utility_in(m, root, cp, side, 0, 0.0, 0.85)
        distribute(m, root, cp, side, 0, 0.45, 0.9, hall=False, feeders=())
        utility_in(m, root, cp, side, 1, 0.0, 0.5)
        distribute(m, root, cp, side, 1, 0.0, 0.85)
        utility_in(m, root, cp, side, 4, 0.0, 0.85)
        distribute(m, root, cp, side, 4, 0.1, 0.85, hall=False, feeders=())
        utility_in(m, root, cp, side, 5, 0.0, 0.1, end=LOST)
        distribute(m, root, cp, side, 5, 0.0, 0.1, end=LOST, hall=False)
        gen_in(m, root, cp, side, 5, 0.5, 0.9)
        distribute(m, root, cp, side, 5, 0.55, 0.9, mt="gen_e")
        gen_in(m, root, cp, side, 6, 0.0, 0.3, end=XFER_BACK)
        distribute(m, root, cp, side, 6, 0.0, 0.3, mt="gen_e", end=XFER_BACK)
        utility_in(m, root, cp, side, 6, 0.2, 0.85)
        distribute(m, root, cp, side, 6, 0.4, 0.9)
    # beat 2: lineup A close-up; a fault on feeder 1's cable
    distribute(m, root, cp, "A", 2, 0.0, 0.9, hall=False, skip=("f1",))
    beads(root, "f1A2", D.through_cab(A["f1"], 1), m["mv"], 2, 0.0, 0.12, size=4.0, speed=8.0, n=2, end=FAULT)
    fx = A["f1"]["c"]
    fault_pt = (fx, 8, D.LINE_ZF + 70)
    W["fault"] = fault_pt
    for k in range(3):
        beads(root, f"fault{k}", D.through_cab(A["f1"], k) + [(fx, 8, D.LINE_ZF + 20), fault_pt], m["fault"], 2, 0.18, 0.3,
              size=4.5, speed=18.0, n=3, end=TRIP + 2)
    flash = empty("fault_flash", root)
    D.ellipsoid("fault_flash_b", fault_pt, 22, 16, 22, m["plasma"], flash)
    D.ellipsoid("fault_flash_c", fault_pt, 9, 22, 9, m["arc"], flash)
    show(flash, [(FAULT, TRIP + 3)])
    # beat 3: both paths, then A off for service
    for side in ("A", "B"):
        utility_in(m, root, cp, side, 3, 0.0, 0.85, end=SERVICE if side == "A" else None)
        distribute(m, root, cp, side, 3, 0.0, 0.85, end=SERVICE if side == "A" else None)

    tags = {
        0: [("utility transformers", cp["TA"]["tank"]), ("line from the substation", cp["TB"]["frame"]),
            ("medium-voltage cable", cp["paths"]["mvA"][6]), ("switchgear house", (0, 320, D.HOUSE_Z1 - 20))],
        1: [("main bus: copper bars", (-760, D.BUS_Y[2] + 8, D.LINE_ZF - 150)), ("feeder breakers", (720, 236, D.LINE_ZF)),
            ("unit substation: to 480 V", cp["UA"]["txc"]), ("480 V to the hall", cp["paths"]["lvB"][6]),
            ("feeds to other halls", (-700, 8, D.HOUSE_Z1 - 60))],
        2: [("fault on feeder 1's cable", fault_pt), ("its relay trips", A["f1"]["relay"]),
            ("vacuum breaker opens", A["f1"]["bottle"]), ("other feeders stay on", A["f3"]["relay"])],
        3: [("path A", cp["paths"]["feedA"][5]), ("path B", cp["paths"]["feedB"][5]),
            ("each rack fed from A and B", cp["hall"]["racks"])],
        4: [("standby generators", cp["GA"]["top"]), ("ATS controller", cp["house"]["ats"]),
            ("utility still feeding", cp["paths"]["mvB"][6])],
        5: [("utility lost", cp["paths"]["mvA"][6]), ("generators start: ~10 s", cp["GB"]["top"]),
            ("ATS: generator breakers close", (0, 236, D.LINE_ZF)), ("UPS carries the gap", cp["hall"]["ups"]["A"]["top"])],
        6: [("utility back", cp["paths"]["mvA"][6]), ("load transfers back", (0, 236, D.LINE_ZF)),
            ("generators cool down", cp["GB"]["top"])],
    }
    for i, items in tags.items():
        for text, pos in items:
            LABEL(text, pos, root, beat(i))
    LABEL("A off for service", A["main"]["relay"], root, [(SERVICE, F(4, 0))])
    LABEL("B carries the whole hall", cp["UB"]["txc"], root, [(SERVICE, F(4, 0))])

    CAMERA(root, POSES)
    D.scale_root(root, ROOT)
    return root


POSES = [
    frame((0.0, 120.0, -1850.0), 3900.0, 0.0, 0.62, pad=1.0),
    frame((0.0, 60.0, -620.0), 3500.0, 0.0, 0.85, pad=1.0),
    frame((-930.0, 165.0, -1110.0), 520.0, 0.22, 0.24, pad=1.0),
    frame((0.0, 60.0, -900.0), 3800.0, 0.0, 0.9, pad=1.0),
    frame((0.0, 160.0, -1850.0), 2700.0, 0.0, 0.55, pad=1.0),
    frame((0.0, 60.0, -1050.0), 4300.0, 0.0, 0.92, pad=1.0),
    frame((0.0, 60.0, -1050.0), 4300.0, 0.15, 0.92, pad=1.0),
]


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
