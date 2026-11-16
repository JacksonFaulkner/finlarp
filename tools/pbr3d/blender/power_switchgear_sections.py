"""The SWITCHGEAR node's nine numbered sections (POWER tab), in the picture-and-panel template
(docs/diagram-pages.md). Section N illustrates heading N of tui/src/screens/diagrams_pages/PWR_SWG.txt,
so the menu title, the text panel and the picture agree; heading 10 (Sources) is text only. Three
beats each, one beat is 8 s.

Each section replays overview beats (power_switchgear_overview.py: the same campus, its beads on the
cables, bus bars and breakers) under a camera and tags chosen for its heading, as the zoom-ins do
(power_switchgear_zooms.py, which owns the replay and the export).

Run from the repo root, one section per run (or several in one process):

    blender -b --factory-startup --python tools/pbr3d/blender/power_switchgear_sections.py -- <n>

Writes blender/power_switchgear_section_<n>.blend and assets/power_switchgear_section_<n>.glb.

  1 what happens   power is split, switched and protected: the yard, the feeds, a fault cleared
  2 the parts      CIRCUIT BREAKER, UNIT SUBSTATION, PROTECTION RELAY
  3 a feed, in order  main breaker, feeder breakers, unit substation, low-voltage to the hall
  4 breaking a fault  a short drawn in red; the relay sees it; the vacuum bottle opens
  5 arc flash      the flash at the fault; enclosed gear
  6 redundancy     two paths, each able to carry the whole load
  7 generators and the ATS  the utility drops, the generators take over, and back
  8 who makes it   yard transformers, unit substations, the UPS and busways
  9 chokepoints    more breakers and feeders per rack; each redundant layer doubles the gear
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from power_switchgear_detail import frame  # noqa: E402
from power_switchgear_zooms import play  # noqa: E402

PAGE = "power_switchgear"


def mid(a, b):
    return tuple((x + y) / 2 for x, y in zip(a, b))


def sections(w):
    """section number -> three beats of (overview beat to replay, camera pose, [(tag, point)])."""
    A, UA, P, hall = w["A"], w["UA"], w["paths"], w["hall"]
    f1, fault, main = A["f1"], w["fault"], A["main"]
    ats = w["house"]["ats"]
    return {
        1: [
            (0, frame((0.0, 150.0, -700.0), 2600.0, 0.30, 0.20),
             [("medium-voltage cable", P["mvA"][6]), ("main breaker", main["relay"])]),
            (1, frame(A["f2"]["relay"], 1200.0, 0.30, 0.20),
             [("feeder breakers split the feed", A["f2"]["relay"]), ("unit substation", UA["txc"])]),
            (2, frame(fault, 1000.0, 0.25, 0.20),
             [("a fault on feeder 1", fault), ("its relay trips", f1["relay"])]),
        ],
        2: [
            (1, frame(f1["bottle"], 360.0, 0.30, 0.15),
             [("CIRCUIT BREAKER: vacuum bottle", f1["bottle"])]),
            (1, frame(UA["txc"], 700.0, 0.25, 0.20),
             [("UNIT SUBSTATION: 480 V out", UA["txc"])]),
            (1, frame(f1["relay"], 420.0, 0.20, 0.20),
             [("PROTECTION RELAY", f1["relay"])]),
        ],
        3: [
            (0, frame(main["relay"], 900.0, 0.30, 0.20),
             [("1 MV cable lands", P["mvA"][6]), ("2 main breaker and bus", main["relay"])]),
            (1, frame(mid(A["f2"]["relay"], UA["txc"]), 1400.0, 0.30, 0.20),
             [("3 feeder breakers", A["f2"]["relay"]), ("4 down to 480 V", UA["txc"])]),
            (1, frame(P["lvB"][6], 1400.0, 0.30, 0.20),
             [("5 switchboards to the hall", P["lvB"][6])]),
        ],
        4: [
            (2, frame(fault, 900.0, 0.25, 0.20),
             [("a short: tens of thousands of amps", fault)]),
            (2, frame(f1["relay"], 420.0, 0.25, 0.20),
             [("the relay sees it within a cycle", f1["relay"])]),
            (2, frame(f1["bottle"], 260.0, 0.30, 0.15),
             [("the vacuum bottle opens", f1["bottle"])]),
        ],
        5: [
            (2, frame(fault, 340.0, 0.20, 0.15),
             [("ARC FLASH", fault)]),
            (2, frame(fault, 220.0, -0.30, 0.10),
             [("thousands of degrees", fault)]),
            (2, frame(f1["relay"], 300.0, 0.15, 0.15),
             [("enclosed, so it vents safely", f1["relay"])]),
        ],
        6: [
            (3, frame(P["feedA"][5], 1000.0, 0.30, 0.20),
             [("path A: the whole load", P["feedA"][5])]),
            (3, frame(P["feedB"][5], 1000.0, -0.30, 0.20),
             [("path B: the whole load", P["feedB"][5])]),
            (3, frame(hall["racks"], 1500.0, 0.20, 0.30),
             [("each server takes one feed from each", hall["racks"])]),
        ],
        7: [
            (4, frame(w["GA"]["top"], 1200.0, 0.30, 0.20),
             [("standby generators", w["GA"]["top"]), ("ATS controller", ats)]),
            (5, frame(ats, 700.0, 0.20, 0.20),
             [("utility lost: the ATS moves", ats), ("generator breakers close", ats)]),
            (6, frame(w["GB"]["top"], 1000.0, -0.20, 0.20),
             [("utility back: transfer back", P["mvA"][6]), ("generators cool down", w["GB"]["top"])]),
        ],
        8: [
            (0, frame(w["TA"]["tank"], 1200.0, 0.30, 0.20),
             [("yard transformer", w["TA"]["tank"])]),
            (1, frame(UA["txc"], 700.0, 0.25, 0.20),
             [("unit substation", UA["txc"])]),
            (6, frame(hall["ups"]["A"]["top"], 1200.0, 0.25, 0.20),
             [("UPS and busways", hall["ups"]["A"]["top"])]),
        ],
        9: [
            (3, frame(main["relay"], 800.0, 0.30, 0.20),
             [("more breakers per feed", main["relay"])]),
            (3, frame(hall["racks"], 1500.0, 0.20, 0.30),
             [("each layer of redundancy doubles the gear", hall["racks"])]),
            (6, frame(ats, 700.0, 0.20, 0.20),
             [("transfer switches add up", ats)]),
        ],
    }


def build(n):
    play(f"section_{n}", lambda w: sections(w)[n], page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ns = [int(a) for a in argv] or list(range(1, 10))
    for n in ns:
        if n not in range(1, 10):
            raise SystemExit("usage: ... -- <1..9>")
        build(n)
