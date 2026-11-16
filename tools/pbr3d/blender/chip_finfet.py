"""CHIP pictures for the FINFET node: the overview, zoom-ins a-e and sections 1-10.

Run from the repo root (through heavy.sh, one job at a time):

    blender -b --factory-startup --python tools/pbr3d/blender/chip_finfet.py -- [name ...]

With no names it builds everything. Names: overview, zoom_a .. zoom_e, sec1 .. sec10. Each scene
writes blender/chip_finfet_<name>.blend and assets/chip_finfet_<name>.glb (the overview is
assets/chip_finfet.glb). One beat is 8 s.

Every scene is built in chip_finfet_detail.py from the same detailed, nanometre-scale FinFET:
silicon fins out of the STI oxide, the high-k / work-function metal / fill gate wrapping three
sides, nitride spacers and caps, merged diamond source/drain epi and tungsten trench contacts,
cut away so the inside shows, with electrons riding the real current path as beads.

Overview beats (the device is drawn into the whole chip at the NMOS spot, at 0.4x):
  0 whole     the whole chip, the FinFET at the NMOS spot picked out
  1 planar    in on a planar NMOS: the gate lies flat on a flat channel, one face gated
  2 rise      fins rise out of the silicon, then the raised source and drain grow on them
  3 wrap      the gate wraps the fins: cut across the gate and along the middle fin
  4 on        the channel glows and electrons ride from the source contact to the drain contact
  5 whole     gate low; back out to the whole chip

Zoom-ins, three beats each: a making fins (SAQP, fin etch, oxide reveal); b the gate wraps three
sides (high-k, metal, on); c fin count (1, 2, 3 fins); d FinFlex (3-2, 2-2, 2-1 cells); e fin
limits (taller and thinner, leakage and tight gaps, nanosheets).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chip_finfet_detail as DT  # noqa: E402

BEATS = 6  # the overview
ZBEATS = 3  # each zoom-in
SBEATS = 3  # each section

SCENES = {f"zoom_{k}": f for k, f in DT.ZOOMS.items()}
SCENES.update({f"sec{n}": f for n, f in enumerate(DT.SECTIONS, 1)})


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = args or ["overview"] + list(SCENES)
    for name in names:
        if name == "overview":
            DT.overview()
        else:
            SCENES[name]()
