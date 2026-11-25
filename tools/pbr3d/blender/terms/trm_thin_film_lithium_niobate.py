"""TRM_THIN_FILM_LITHIUM_NIOBATE: the Terms-tab overview for thin-film lithium niobate (TFLN).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_thin_film_lithium_niobate.py

Writes assets/term_TRM_THIN_FILM_LITHIUM_NIOBATE.glb. Captions live in
specs/terms/TRM_THIN_FILM_LITHIUM_NIOBATE.json.

Beats:
  0 module     a coherent module with its closed optical case and DSP
  1 film       the TFLN chip cut open: a sub-micron lithium niobate film on oxide and silicon
  2 pockels    the electrodes' voltage changes the crystal's index (the Pockels effect)
  3 chip       the modulator on the chip: light in, phase shift, low loss at high speed
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

SLUG = "TRM_THIN_FILM_LITHIUM_NIOBATE"
BEATS = [
    ("Modulators move from bulk crystal to a chip-thin film",
     "Inside a coherent module, the modulator that writes data onto light can be built from thin-film lithium niobate "
     "(TFLN). The crystal is bonded as a sub-micron layer onto a silicon wafer, so the device shrinks toward chip scale "
     "instead of the centimetres of older lithium niobate modulators."),
    ("A sub-micron crystal film on oxide and silicon",
     "The stack is simple: a silicon base, a layer of oxide, then a lithium niobate film only about 0.6 microns thick, "
     "etched into a ridge that carries the light. Gold electrodes sit either side of the ridge to apply the voltage."),
    ("Voltage bends the crystal's index: the Pockels effect",
     "Lithium niobate changes its refractive index in a straight line with the voltage across it. That is the Pockels "
     "effect. The field between the electrodes is strong because the gap is tiny, so a low drive voltage is enough to "
     "shift the phase of the light and keep the modulator fast."),
    ("On the chip: fast, low loss, and built for 200G per lane",
     "The same ridge is laid out as a Mach-Zehnder, so the light splits, the arms phase-shift and the beams recombine. "
     "The films compete with silicon photonics and indium phosphide for 200G-per-lane and coherent parts. Coherent "
     "(COHR), Lumentum (LITE), HyperLight (private) and Fujitsu's optical unit are the names in play."),
]

CHIP_TOP = 4.0
CX, CZ, L, ARM = 0.0, 0.0, 110.0, 18.0


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)

    # beat 0: the module in context
    ctx = empty("ctx", root)
    K.pcb(m, ctx, "pcb", -90.0, 90.0, -60.0, 40.0)
    dsp = (-40.0, 1.6, 0.0)
    K.dsp(m, ctx, "dsp", dsp, 26.0, 22.0)
    mod = (30.0, 1.6, 0.0)
    K.module(m, ctx, "mod", mod, 44.0, 10.0, 30.0, cut=False)
    K.fiber(m, ctx, "fib", [(52.0, 6.0, 0.0), (72.0, 10.0, 0.0), (94.0, 4.0, -16.0)])
    show(ctx, [(F(0, 0), F(1, 0))])

    # beat 1-2: the cross-section, cut open
    xs = K.tfln_xsec(m, root, "xs", 0.0, 0.0, 0.0, 120.0, w=2.4)
    show(xs["group"], [(F(1, 0), F(4, 0))])
    show(xs["field"], [(F(2, 0.1), F(3, 0))])
    for s in (1, -1):
        p = [(-50.0, 7.0, s * 6.0), (50.0, 7.0, s * 6.0)]
        run(root, f"drv{s}", p, 4, 1.6, m["ph_amber"], 2, 0.1, 0.8, 30)

    # beat 3: the TFLN modulator on a chip, light through the ridge arms
    chip = empty("chip", root)
    K.pic(m, chip, "chip", -CX - 65.0, CX + 65.0, -35.0, 35.0, y=0.0)
    mz = K.mzm(m, chip, "mzm", CX, CZ, L, ARM, CHIP_TOP, ln=True)
    show(chip, [(F(3, 0), F(4, 0))])
    show(xs["group"], [(F(1, 0), F(3, 0))])
    path_t = mz["in"] + mz["arms"][1][1:] + mz["out"][1:]
    path_b = mz["in"] + mz["arms"][-1][1:] + mz["out"][1:]
    light = empty("light", root)
    run(light, "lt", path_t, 5, 2.2, m["ph_cyan"], [3], 0.0, 0.5, 30)
    run(light, "lb", path_b, 5, 2.2, m["ph_cyan"], [3], 0.0, 0.5, 30)

    tags = {
        0: [("DSP: sets the bits", (dsp[0], 6.0, dsp[2])), ("TFLN modulator inside", (mod[0], 12.0, mod[2])),
            ("fibre out", (94.0, 6.0, -16.0))],
        1: [("lithium niobate film, ~0.6 um", xs["pts"]["film"]), ("ridge carries the light", xs["pts"]["ridge"]),
            ("silicon base", xs["pts"]["sub"])],
        2: [("gold electrodes: data", xs["pts"]["elec"]), ("index shifts with voltage", xs["pts"]["ridge"]),
            ("Pockels effect", (0.0, 9.0, 0.0))],
        3: [("light in, split to arms", mz["pts"]["split"]), ("low loss, fast phase shift", mz["pts"]["top"]),
            ("COHR, LITE, HyperLight", (CX + 40.0, CHIP_TOP + 10.0, CZ))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((0.0, 0.0, 0.0), 160.0, 0.30, 0.40, pad=1.0),
        frame((0.0, 3.0, 0.0), 130.0, 0.25, 0.20),
        frame((0.0, 3.0, 0.0), 110.0, -0.15, 0.30),
        frame((0.0, CHIP_TOP, 0.0), 175.0, 0.10, 0.55),
    ], root)


if __name__ == "__main__":
    build()
