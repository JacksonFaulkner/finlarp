"""CHIP pictures for the GATE-ALL-AROUND node: the overview, zoom-ins a-e and sections 1-10.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/chip_gaa.py [-- overview a 3 ...]

With no arguments it writes everything: the overview (assets/chip_gaa.glb), zoom-ins a-e
(assets/chip_gaa_zoom_<key>.glb) and sections 1-10 (assets/chip_gaa_sec<N>.glb). Named arguments
after `--` pick scenes: `overview`, `a`..`e`, or a section number. One beat is 8 s.

Every scene is built in chip_gaa_detail.py from the same detailed, nanometre-scale nanosheet
transistor: three silicon sheets on a mesa, inner spacers, high-k and metal in every gap,
nitride spacers and cap, source/drain epi and trench contacts, cut away so the inside shows,
with electrons riding each sheet as beads.

Overview beats (the device is drawn into the whole chip at the NMOS spot, at 0.4x):
  0 whole     the whole chip, the GAA transistor at the NMOS spot picked out
  1 stack     in on the transistor, cut along the channel: epi, three sheets, gate between them
  2 wrap      cut across the gate as well: the gate round all four sides of each sheet
  3 current   electrons ride from the source contact through every sheet to the drain contact
  4 wide      a wide sheet stack, cut across the gate: more drive
  5 narrow    a narrow one: less leakage and area
  6 whole     back out to the whole chip

Zoom-ins: a the process flow (3 beats); b release (3); c sheet width (3); d backside power (3);
e roadmap: FinFET, nanosheet, forksheet, CFET (4).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chip_gaa_detail as DT  # noqa: E402

ZOOMS = DT.ZOOMS
SECTIONS = DT.SECTIONS


if __name__ == "__main__":
    picks = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not picks:
        picks = ["overview", *ZOOMS, *[str(n) for n in range(1, 11)]]
    for pick in picks:
        if pick == "overview":
            DT.overview()
        elif pick in ZOOMS:
            ZOOMS[pick]()
        else:
            SECTIONS[int(pick) - 1]()
