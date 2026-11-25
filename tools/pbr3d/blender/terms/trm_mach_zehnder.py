"""TRM_MACH_ZEHNDER: the Terms-tab overview for the Mach-Zehnder modulator.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_mach_zehnder.py

Writes assets/term_TRM_MACH_ZEHNDER.glb. Captions live in specs/terms/TRM_MACH_ZEHNDER.json.

Beats:
  0 module     a coherent module: DSP chip, the closed optical module, fibre out
  1 split      the chip, cut open: light enters, splits into two arms
  2 drive      the data voltage on the gold electrodes shifts the phase of one arm
  3 recombine  the arms meet: in phase reads as a 1, out of phase as a 0
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from sand_overview import F, empty, show  # noqa: E402
from power_vrm_detail import bx, blink, frame, run  # noqa: E402

import term_common as C  # noqa: E402
import kit_photonics as K  # noqa: E402

SLUG = "TRM_MACH_ZEHNDER"
BEATS = [
    ("A coherent module turns electrical data into light",
     "Inside an 800G or 1.6T optical module, a DSP chip prepares the bits and a Mach-Zehnder modulator (MZM) "
     "writes them onto a laser beam. The light then leaves through fibre. MZMs are the standard modulator in "
     "coherent optics and in many of these transceivers."),
    ("The chip splits the light into two arms",
     "The MZM is a small chip with a waveguide that splits the laser light into two paths, each a channel only a "
     "few microns wide. The two arms are the same length, so the light in them starts in step."),
    ("Voltage on each arm shifts its phase",
     "The data signal drives gold electrodes that run along the arms. Voltage changes the refractive index in an arm, "
     "so the light there is delayed by a fraction of a wavelength. The drive needs more power than a micro-ring "
     "modulator, but the device holds its performance better across temperature."),
    ("The arms recombine: in phase reads as a 1, out of phase as a 0",
     "When the two beams meet again they add or cancel, so the output swings between bright and dark. Silicon "
     "photonics, indium phosphide and lithium niobate chips all use this layout. Coherent (COHR), Lumentum (LITE), "
     "Marvell (MRVL) and Broadcom (AVGO) are the names to watch."),
]

CX, CZ, L, ARM = 0.0, 0.0, 110.0, 18.0
CHIP_TOP = 4.0


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)

    # beat 0: the module in context, on a board with its DSP
    ctx = empty("ctx", root)
    K.pcb(m, ctx, "pcb", -90.0, 90.0, -60.0, 40.0)
    dsp = (-40.0, 1.6, 0.0)
    K.dsp(m, ctx, "dsp", dsp, 26.0, 22.0)
    mod = (30.0, 1.6, 0.0)
    K.module(m, ctx, "mod", mod, 44.0, 10.0, 30.0, cut=False)
    K.fiber(m, ctx, "fib", [(52.0, 6.0, 0.0), (72.0, 10.0, 0.0), (94.0, 4.0, -16.0)])
    show(ctx, [(F(0, 0), F(1, 0))])

    # beats 1-3: the chip, cut open, large on the bench
    chip = empty("chip", root)
    K.pic(m, chip, "chip", -CX - 65.0, CX + 65.0, -35.0, 35.0, y=0.0)
    mz = K.mzm(m, chip, "mzm", CX, CZ, L, ARM, CHIP_TOP)
    show(chip, [(F(1, 0), F(4, 0))])

    # beats 1-3: light enters, splits, recombines
    path_t = mz["in"] + mz["arms"][1][1:] + mz["out"][1:]
    path_b = mz["in"] + mz["arms"][-1][1:] + mz["out"][1:]
    light = empty("light", root)
    run(light, "lt", path_t, 5, 2.2, m["ph_cyan"], [1, 2, 3], 0.0, 0.7, 40)
    run(light, "lb", path_b, 5, 2.2, m["ph_cyan"], [1, 2, 3], 0.0, 0.7, 40)

    # beat 2: amber drive beads ride over each arm's electrodes
    drv = empty("drive", root)
    for s in (1, -1):
        p = [(x, CHIP_TOP + 3.0, z) for (x, _, z) in mz["arms"][s][7:-7]]
        run(drv, f"drv{s}", p, 4, 1.6, m["ph_amber"], 2, 0.1, 0.8, 30)

    # beat 3: four output bits, each on in its own slot: 1 0 1 0
    bits = []
    for k in range(4):
        b = bx(f"bit{k}", (66.0 + 6.0 * k, CHIP_TOP + 3.0, CZ - 3.0), (69.0 + 6.0 * k, CHIP_TOP + 6.0, CZ + 3.0), m["ph_green"], root)
        bits.append(b)
    for k, on in enumerate((1, 0, 1, 0)):
        if on:
            blink(bits[k], 3, [k], n=4, on=0.9)
        else:
            show(bits[k], [])

    tags = {
        0: [("DSP: sets the bits", (dsp[0], 6.0, dsp[2])), ("800G / 1.6T module", (mod[0], 12.0, mod[2])),
            ("fibre out", (94.0, 6.0, -16.0))],
        1: [("input laser light", mz["pts"]["in"]), ("waveguide splits it", mz["pts"]["split"]),
            ("two arms, same length", mz["pts"]["top"])],
        2: [("gold electrodes: data", (CX, CHIP_TOP + 6.0, CZ + ARM + 2.6)), ("arm index shifts", mz["pts"]["top"]),
            ("phase = delay", mz["pts"]["bot"])],
        3: [("in phase: bright 1", mz["pts"]["out"]), ("out of phase: dark 0", mz["pts"]["recomb"]),
            ("COHR, LITE, MRVL, AVGO", (CX + 40.0, CHIP_TOP + 10.0, CZ))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((0.0, 0.0, 0.0), 160.0, 0.30, 0.40, pad=1.0),
        frame((0.0, CHIP_TOP, 0.0), 150.0, 0.25, 0.55),
        frame((0.0, CHIP_TOP, 0.0), 150.0, -0.15, 0.50),
        frame((0.0, CHIP_TOP, 0.0), 175.0, 0.10, 0.55),
    ], root)


if __name__ == "__main__":
    build()
