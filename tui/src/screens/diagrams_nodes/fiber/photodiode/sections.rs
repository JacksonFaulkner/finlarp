// PHOTODIODE: numbered sections 1-9, one per heading of diagrams_pages/FIB_PD.txt (tools/pbr3d/blender/
// fiber_photodiode_sections.py, GLBs in tools/pbr3d/assets/fiber_photodiode_section_<n>.glb), three beats each.
// The receiver is drawn about 16x life size (fiber_photodiode_detail.py), the chip's layers far thicker still.

use super::super::super::blender::{Cell, page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static S1: Cell = std::sync::OnceLock::new();
static S2: Cell = std::sync::OnceLock::new();
static S3: Cell = std::sync::OnceLock::new();
static S4: Cell = std::sync::OnceLock::new();
static S5: Cell = std::sync::OnceLock::new();
static S6: Cell = std::sync::OnceLock::new();
static S7: Cell = std::sync::OnceLock::new();
static S8: Cell = std::sync::OnceLock::new();
static S9: Cell = std::sync::OnceLock::new();

/// 1. What happens: each photon becomes a little bit of current.
const S1_B: &[Beat] = &[
    Beat::new("LIGHT LANDS on the PIN photodiode", BEAT_MS)
        .note(
            "Light leaving the fibre spreads across a small gap, and a ball lens in the can's cap focuses it onto a PIN photodiode chip. Everything is drawn about 16 times life size, and the can is cut open so the chip shows.",
            "The gold ferrule at left, the orange cone through the clear ball lens, narrowing onto the layered chip inside the cut-open steel can.",
        )
        .detail(
            "The photodiode is where light turns back into electricity.",
            &["PIN: p-type, intrinsic, n-type layers", "Absorber: InGaAs on an InP chip"],
        ),
    Beat::new("PHOTONS free ELECTRONS and HOLES", BEAT_MS)
        .note(
            "The chip's middle layer, InGaAs, absorbs the photons. Each one frees an electron and a hole, and a reverse voltage across the diode sweeps them to opposite contacts. That flow is a current of microamps that rises and falls with the light's PAM4 levels.",
            "White flashes in the yellow InGaAs; cyan electrons drift right to the blue n side and its gold pad, violet holes drift left to the pink p side and the gold ring.",
        )
        .detail(
            "More light, more current: the current copies the light.",
            &["One photon -> one electron-hole pair", "Current: microamps, following the PAM4 levels"],
        ),
    Beat::new("TIA: current becomes a voltage", BEAT_MS)
        .note(
            "A TIA beside the photodiode turns the current into a voltage for the DSP. In silicon-photonics receivers the absorber is germanium grown on the silicon chip instead of InGaAs.",
            "Cyan beads run along the gold bond wire into the dark TIA; amber beads leave it and run out along the OUT pin.",
        )
        .detail(
            "Light -> current -> voltage -> DSP.",
            &["TIA: transimpedance amplifier", "Silicon photonics: germanium absorber"],
        ),
];

/// 2. The parts: the PIN's layers, the TIA, a germanium photodiode on silicon.
const S2_B: &[Beat] = &[
    Beat::new("PIN PHOTODIODE and its INGAAS", BEAT_MS)
        .note(
            "A PIN photodiode is three layers: p-type, intrinsic (the absorber) and n-type, run reverse biased. Here the intrinsic layer is InGaAs (indium gallium arsenide), which absorbs the 1310 and 1550 nm light that silicon can't, grown on an indium phosphide chip.",
            "The chip's cut face: pink p-InP, yellow InGaAs absorber, blue n-InP, grey InP substrate on a white ceramic submount; pairs splitting in the yellow layer.",
        )
        .detail(
            "Only the yellow middle layer absorbs the light.",
            &["p / intrinsic / n, reverse biased", "InGaAs absorbs 1310 and 1550 nm"],
        ),
    Beat::new("TIA: current in, voltage out", BEAT_MS)
        .note(
            "The TIA (transimpedance amplifier) is a small chip right beside the photodiode. Its input takes the photodiode's current over a short gold bond wire; its output is a voltage. How much current it gets is the diode's responsivity: close to 1 A/W for InGaAs.",
            "The dark TIA die with its gold pads; cyan beads run up the bond wire into it, amber beads leave on the second wire.",
        )
        .detail(
            "Diode and TIA together set speed and noise.",
            &["Responsivity: close to 1 A/W for InGaAs", "TIA: current in, voltage out"],
        ),
    Beat::new("GERMANIUM on silicon", BEAT_MS)
        .note(
            "Silicon-photonics receivers grow germanium on the silicon chip itself. Light arrives along a silicon waveguide and is absorbed in the germanium block on its end; gold contacts on the top and on the doped silicon below collect the electrons and holes.",
            "A grey silicon chip with a pale silicon waveguide rib; the brown germanium block on its end, blue n cap and two gold contacts; photons along the rib, flashes and carriers in the germanium.",
        )
        .detail(
            "Made in the same fab as the silicon modulators.",
            &["Germanium: absorber grown on silicon", "Light comes in along a waveguide"],
        ),
];

/// 3. Light becomes a voltage, in order: the six steps.
const S3_B: &[Beat] = &[
    Beat::new("STEPS 1-2: focus, absorb", BEAT_MS)
        .note(
            "Step 1: a lens focuses light from the fibre onto the photodiode. Step 2: the photons are absorbed in the InGaAs layer.",
            "The orange cone through the ball lens, narrowing onto the chip; photons crossing the can and flashes in the yellow layer.",
        )
        .detail(
            "Everything starts with getting light onto a tiny target.",
            &["1 lens focuses the light", "2 photons absorbed in InGaAs"],
        ),
    Beat::new("STEPS 3-4: pair, current", BEAT_MS)
        .note(
            "Step 3: each absorbed photon frees an electron and a hole. Step 4: the reverse bias sweeps them to the contacts, electrons to the n side and holes to the p side, and that flow is the current.",
            "Close on the chip: violet holes drifting left to the pink p layer and gold ring, cyan electrons drifting right into the blue n layer and down to the gold n pad.",
        )
        .detail(
            "Charge moving to the contacts is the photocurrent.",
            &["3 one electron + one hole each", "4 bias sweeps them: current"],
        ),
    Beat::new("STEPS 5-6: TIA, DSP", BEAT_MS)
        .note(
            "Step 5: the TIA turns the current into a voltage. Step 6: the DSP equalizes it and decides each PAM4 level. Here the can sits in a pluggable module: the voltage leaves the pins, crosses a flex and runs along a PCB trace to the DSP.",
            "Pulled back inside the open module: amber beads leave the can's pins, cross the orange flex and run along the copper trace to the DSP package on the green PCB.",
        )
        .detail(
            "Light became current, then voltage, then bits.",
            &["5 TIA: current to voltage", "6 DSP decides each PAM4 level"],
        ),
];

/// 4. Why InGaAs (and germanium).
const S4_B: &[Beat] = &[
    Beat::new("SILICON: 1310 nm goes straight through", BEAT_MS)
        .note(
            "Silicon is transparent to light longer than about 1.1 um, so it can't detect 1310 or 1550 nm: the photons pass through without freeing any charge. That is why the cheap silicon photodiodes used for visible light don't work in fibre receivers.",
            "A fibre source on a post shines orange photons into a grey silicon slab; they come out the far side untouched.",
        )
        .detail(
            "Silicon's bandgap is too wide for these photons.",
            &["Silicon: transparent past ~1.1 um", "Data-centre links: 1310 nm"],
        ),
    Beat::new("INGAAS: absorbed, pairs freed", BEAT_MS)
        .note(
            "InGaAs, grown on InP, absorbs 1310 and 1550 nm strongly. Each photon stops in the layer and frees an electron and a hole, which is the start of the current.",
            "The same source into a yellow InGaAs layer on a grey InP block: each photon ends in a white flash, and a cyan electron and violet hole move apart.",
        )
        .detail(
            "InGaAs is the standard absorber for fibre receivers.",
            &["InGaAs on InP absorbs 1310 and 1550 nm", "One photon -> one pair"],
        ),
    Beat::new("BANDGAPS against the photon", BEAT_MS)
        .note(
            "A material absorbs a photon only if the photon carries more energy than its bandgap. A 1310 nm photon carries about 0.95 eV: below silicon's 1.12 eV, above InGaAs's and germanium's. Silicon photonics grows germanium on the silicon chip for that reason, made in the same fab as the modulators.",
            "Three bars on a bench, as tall as each bandgap: grey silicon, yellow InGaAs, brown germanium. The glowing orange line at the photon's energy runs below the silicon bar's top and over the other two.",
        )
        .detail(
            "Bar above the line: blind. Bar below: absorbs.",
            &["1310 nm photon ~0.95 eV", "Si 1.12 eV; InGaAs ~0.75 eV; Ge ~0.66 eV"],
        ),
];

/// 5. Responsivity and speed.
const S5_B: &[Beat] = &[
    Beat::new("RESPONSIVITY: ~1 A/W", BEAT_MS)
        .note(
            "Responsivity is current out per watt of light in. Near 1 A/W, a milliwatt of light gives about a milliamp, and the current follows the light up and down.",
            "The cut can on a board beside two glass gauges: the orange light gauge and the cyan current gauge rise and fall together, almost level.",
        )
        .detail(
            "Close to 1 A/W for InGaAs.",
            &["~1 A/W: 1 mW in -> ~1 mA out", "Current tracks light power"],
        ),
    Beat::new("SPEED: tiny diode, fast TIA", BEAT_MS)
        .note(
            "To follow 106 GBd symbols the photodiode must be tiny, so its capacitance is small, and the TIA must have the bandwidth to match. Every symbol's light has to become its own current pulse before the next arrives.",
            "Bursts of photons cross the can; a separate amber pulse runs out along the OUT pin for each one, closely spaced.",
        )
        .detail(
            "Smaller diode, lower capacitance, faster.",
            &["106 GBd symbols", "Small diode = small capacitance"],
        ),
    Beat::new("SMALLER is harder to hit", BEAT_MS)
        .note(
            "A smaller photodiode is faster but harder to hit with the light. If the focused spot is wider than the window, the edges of the beam land on the contact ring and are lost.",
            "Close on the chip: photons inside the ring's opening make pairs; photons at the edge stop on the gold ring with a red flash.",
        )
        .detail(
            "Speed trades against how easily light lands.",
            &["Faster = smaller window", "Light outside the window is lost"],
        ),
];

/// 6. Noise and sensitivity.
const S6_B: &[Beat] = &[
    Beat::new("FOUR PAM4 LEVELS at the TIA's output", BEAT_MS)
        .note(
            "PAM4 sends four light levels, so the TIA's output should sit at four voltage levels. With plenty of light and little noise, each sample lands right on its level and the DSP can tell them apart.",
            "A cable runs from the OUT pin to a readout standing on the board; amber samples slide along four grey level lines, each right on its line.",
        )
        .detail(
            "Four levels = two bits per symbol.",
            &["PAM4: 4 levels", "Clean levels: easy decisions"],
        ),
    Beat::new("NOISE blurs the levels", BEAT_MS)
        .note(
            "The TIA's noise and the photodiode's shot noise add random jitter to every sample, blurring the four levels into bands.",
            "The same readout, now each amber sample jumps above and below its line; tags on the TIA and the chip name the two noise sources.",
        )
        .detail(
            "Noise is set by the TIA and the photodiode.",
            &["TIA noise", "Photodiode shot noise"],
        ),
    Beat::new("WEAK LIGHT: levels overlap", BEAT_MS)
        .note(
            "With less light the four levels sit closer together but the noise doesn't shrink, so samples start landing nearer the wrong level: errors. The weakest light the receiver can still decode at its error-rate target is its sensitivity. PAM4 levels are a third as far apart as NRZ's, so PAM4 needs more light for the same error rate.",
            "Close on the readout: the four lines squeezed together, the jittering samples crossing between them.",
        )
        .detail(
            "Sensitivity: the least light that still decodes.",
            &["PAM4 levels 1/3 as far apart as NRZ", "PAM4 needs more light than NRZ"],
        ),
];

/// 7. The link budget.
const S7_B: &[Beat] = &[
    Beat::new("LINK BUDGET: from the laser", BEAT_MS)
        .note(
            "The link budget starts at the laser's output power and subtracts every loss on the way to the photodiode. The glowing line above the link is the light's power at each point; it steps down at the first connector.",
            "A laser can at left, a yellow patch cord with a blue connector pair; the orange power line starts high above the laser and drops at the connector.",
        )
        .detail(
            "Every connector costs power.",
            &["Connectors: often ~0.5 dB each"],
        ),
    Beat::new("FIBRE and CONNECTORS", BEAT_MS)
        .note(
            "The fibre loses a little along its length, 0.32 dB per km at 1310 nm, so over data-centre distances the glass barely matters. Each connector takes a bigger bite. Inside a data centre the connectors, not the glass, use most of the budget.",
            "The power line slopes gently along the fibre, then steps down again at the second connector.",
        )
        .detail(
            "Clean connectors matter more than the glass.",
            &["Fibre: 0.32 dB/km at 1310 nm", "Connectors use most of the budget"],
        ),
    Beat::new("ABOVE SENSITIVITY, with margin", BEAT_MS)
        .note(
            "What reaches the photodiode must stay above the receiver's sensitivity, with margin for aging, temperature and dirty connectors.",
            "The power line ends above the photodiode can; the red line below it is the receiver's sensitivity, and the amber bar between them is the margin.",
        )
        .detail(
            "Out of margin = errors.",
            &["Laser - losses > sensitivity + margin"],
        ),
];

/// 8. Who makes it.
const S8_B: &[Beat] = &[
    Beat::new("PHOTODIODES", BEAT_MS)
        .note(
            "InGaAs photodiode chips come from Coherent, Lumentum and Hamamatsu, and from module makers' own in-house lines.",
            "The chip framed in a glowing outline inside the cut can, tagged with its makers.",
        )
        .detail(
            "A few suppliers for the light-sensitive chip.",
            &["Coherent (COHR), Lumentum (LITE)", "Hamamatsu; in-house module lines"],
        ),
    Beat::new("TIAS", BEAT_MS)
        .note(
            "The TIAs that sit beside them come from MACOM, Semtech, Marvell and Broadcom.",
            "The dark TIA die framed in a glowing outline, a tag at each corner; current beads run up its bond wire.",
        )
        .detail(
            "Analog chip makers own the TIA.",
            &["MACOM (MTSI), Semtech (SMTC)", "Marvell (MRVL), Broadcom (AVGO)"],
        ),
    Beat::new("GERMANIUM comes with the chip", BEAT_MS)
        .note(
            "Germanium photodiodes aren't bought separately: they come with the silicon-photonics chips, grown in the same fab as the modulators.",
            "The germanium-on-silicon photodiode framed in a glowing outline: light along the waveguide, carriers out through the gold contacts.",
        )
        .detail(
            "In silicon photonics the detector is part of the chip.",
            &["Ge PD: part of the SiPh chip"],
        ),
];

/// 9. Chokepoints and risks.
const S9_B: &[Beat] = &[
    Beat::new("FASTER LANES: smaller diode, faster TIA", BEAT_MS)
        .note(
            "Each step up in lane speed needs a smaller, lower-capacitance photodiode and a faster TIA, and both are hard to make well.",
            "Close on the chip and the TIA in the cut can; current beads race up the bond wire into the TIA.",
        )
        .detail(
            "Speed is set at the diode and the TIA.",
            &["Smaller, lower-capacitance photodiode", "Faster TIA"],
        ),
    Beat::new("LPO: the DSP comes out", BEAT_MS)
        .note(
            "Linear pluggable optics (LPO) remove the DSP from the module. The TIA's output then goes straight onto the host's SerDes, so the TIA and the switch chip have to do the clean-up the DSP used to do.",
            "Inside the open module the DSP package disappears; amber beads run from the can's pins, across the flex and straight down the trace to the gold card-edge fingers.",
        )
        .detail(
            "Less power and cost, but less margin for error.",
            &["LPO: no DSP in the module", "TIA output -> host SerDes"],
        ),
    Beat::new("DIRTY CONNECTORS eat the budget", BEAT_MS)
        .note(
            "Dirty or worn connectors eat the link budget. A speck of dust on a ferrule's end face blocks part of the light right at the joint, a loss no amount of good glass can make up.",
            "A patch cord's white ferrule meets the port's ferrule; dark dust specks sit on its end face. Photons that hit them stop with a red flash; the rest cross the gap.",
        )
        .detail(
            "Clean connectors are the cheapest margin.",
            &["Connectors: most of the DC budget", "Dust on a ferrule blocks light"],
        ),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_photodiode_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_photodiode_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_photodiode_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_photodiode_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_photodiode_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_photodiode_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_photodiode_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_photodiode_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_photodiode_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
