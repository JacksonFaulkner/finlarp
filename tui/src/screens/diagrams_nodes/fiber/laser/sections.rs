// LASER: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/FIB_LASER.txt, from the Blender scenes in
// tools/pbr3d/blender/fiber_laser_sections.py (GLBs in tools/pbr3d/assets/fiber_laser_section_<n>.glb). Three beats each.
// The parts (EML, VCSEL, silicon-photonics chip with its Mach-Zehnder modulator, lens, ferrule, wafers) are drawn far
// larger than life and cut open at the front so their insides show.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static S1: Cell = std::sync::OnceLock::new();
static S2: Cell = std::sync::OnceLock::new();
static S3: Cell = std::sync::OnceLock::new();
static S4: Cell = std::sync::OnceLock::new();
static S5: Cell = std::sync::OnceLock::new();
static S6: Cell = std::sync::OnceLock::new();
static S7: Cell = std::sync::OnceLock::new();
static S8: Cell = std::sync::OnceLock::new();
static S9: Cell = std::sync::OnceLock::new();

/// 1 what happens: the driver gets the DSP's symbols, the EML makes and dims the light, a lens puts it in the fibre.
const S1_B: &[Beat] = &[
    Beat::new("the driver gets the DSP's symbols", BEAT_MS)
        .note(
            "The PAM4 DSP sends a clean stream of symbols to a laser driver chip. The driver turns each symbol into the voltage or current the light source needs, and passes it to the laser chip over short wires. It also feeds the laser a steady bias current.",
            "Blue dots run along the copper traces on the green board into the black driver IC. Pink dots, the data, leave it along one trace and up a gold bond wire onto the laser chip at the right; the other wire carries the steady bias.",
        )
        .detail(
            "The driver is the bridge from electronics to light.",
            &["DSP: clean PAM4 symbols", "Driver: one signal per symbol", "Plus a steady bias for the laser"],
        ),
    Beat::new("an EML makes the light and dims it", BEAT_MS)
        .note(
            "In a single-mode module the light source is usually an EML. Its DFB laser section makes steady light, and a modulator section on the same chip dims that light to one of four levels for each PAM4 symbol. Short multimode links use a VCSEL switched directly instead, and silicon-photonics modules use a separate CW laser and a silicon modulator.",
            "The stripe along the cut-open chip glows; pink data dots arrive on the modulator's pad, and the glow at the chip's right end steps between four sizes as an orange cone of light leaves it.",
        )
        .detail(
            "One chip: steady light, then switched to the data.",
            &["EML = DFB laser + modulator", "Four brightness levels: PAM4", "VCSEL / CW laser: the other routes"],
        ),
    Beat::new("a lens puts the light into the fibre", BEAT_MS)
        .note(
            "The light leaves the chip spreading out. A lens gathers it and focuses it onto the tiny core of the fibre, held in a ceramic ferrule. From there each symbol travels as a pulse of light at its own brightness.",
            "The orange cone widens into the clear lens in its grey holder, then narrows into the end of the white ferrule inside its gold sleeve. Glowing pulses of four different brightnesses run down the fibre to the right.",
        )
        .detail(
            "Each symbol is now a pulse of light.",
            &["Lens: focuses onto the fibre core", "One pulse brightness per symbol"],
        ),
];

/// 2 the parts: the EML cut open: InP, quantum wells, the DFB grating, the modulator.
const S2_B: &[Beat] = &[
    Beat::new("an EML: InP, cut open", BEAT_MS)
        .note(
            "This is an EML (electro-absorption modulated laser): a DFB laser and a modulator on one chip. It is made of indium phosphide (InP), the semiconductor single-mode lasers are made of. Silicon can't emit light itself, which is why even silicon photonics needs an InP laser.",
            "The chip is cut down its middle. The dark grey bulk is the InP; the thin pink line is the layer that makes light, the cyan teeth above it are the grating, the green band at the right is the modulator. Two gold pads sit on top; the white slab under it is the submount.",
        )
        .detail(
            "InP is the material every single-mode laser needs.",
            &["EML: DFB laser + modulator, one chip", "INDIUM PHOSPHIDE: InP", "Silicon can't emit light itself"],
        ),
    Beat::new("the DFB grating locks one wavelength", BEAT_MS)
        .note(
            "Current through thin quantum-well layers makes light. A grating etched just above them, a row of tiny ridges, reflects only one wavelength back and forth, so the laser emits one clean colour: that is the DFB (distributed feedback) laser. A raised ridge keeps the light in a narrow stripe.",
            "The stripe glows white-orange along the cut face, the cyan grating teeth sit just above it, and dots of light run along the stripe.",
        )
        .detail(
            "One wavelength keeps pulses sharp in the fibre.",
            &["DFB: grating sets the WAVELENGTH", "1310 nm (O-band) for data-center single-mode"],
        ),
    Beat::new("two sections: laser, then modulator", BEAT_MS)
        .note(
            "The left section is the DFB laser, running steadily. The right section is the electro-absorption modulator: it absorbs more or less of the light to set each level. A CW laser is a DFB like the left section on its own: steady light, no data, used to feed a silicon modulator. A monitor photodiode behind the back facet reads the laser's power.",
            "The glow is bright in the left section and softer through the right one. An orange cone leaves the right end; a faint cone from the left end lights the blue face of the monitor photodiode.",
        )
        .detail(
            "The same DFB, with or without a modulator, is the light source of every single-mode route.",
            &["DFB LASER: steady light", "EML: adds the modulator", "CW LASER: the DFB alone, no data"],
        ),
];

/// 3 a symbol becomes light, in order: the five steps from the write-up.
const S3_B: &[Beat] = &[
    Beat::new("1-2: the symbol arrives; the DFB makes steady light", BEAT_MS)
        .note(
            "Step 1: the driver receives a clean PAM4 symbol from the DSP and sends it towards the chip. Step 2: meanwhile its steady bias current flows into the DFB section, which makes steady light at 1310 nm.",
            "A pink dot runs along the lower pin and wire, the symbol. Blue dots run along the upper pin and wire into the left gold pad and down through the chip; the stripe lights and a steady glow sits at the chip's front end.",
        )
        .detail(
            "The laser itself stays on; the data comes next.",
            &["1: symbol from the DSP", "2: steady DFB light at 1310 nm"],
        ),
    Beat::new("3: the modulator dims it to one of four levels", BEAT_MS)
        .note(
            "Step 3: the symbol reaches the modulator section as a voltage. The modulator absorbs part of the light, more or less depending on the voltage, so the light leaving the chip has one of four brightness levels, one per symbol.",
            "Pink dots run along the long arched wire onto the right gold pad. The glow at the chip's front end steps between four sizes.",
        )
        .detail(
            "Four levels carry two bits per symbol.",
            &["3: modulator absorbs part of the light", "Four levels: PAM4"],
        ),
    Beat::new("4-5: into the fibre, power held steady", BEAT_MS)
        .note(
            "Step 4: a lens couples the light into the fibre's core. Step 5: behind the chip, a monitor photodiode catches the little light leaking from the back and reports it to the driver, which keeps the laser's power steady.",
            "First the view follows the orange cone through the lens into the white ferrule and the lit fibre core. Then it swings back: a small cone from the chip's back end lights the blue face of the monitor photodiode, and blue dots run up its wire to a pin.",
        )
        .detail(
            "The loop keeps every level where the receiver expects it.",
            &["4: lens into the fibre core", "5: monitor photodiode holds power steady"],
        ),
];

/// 4 EML, VCSEL, silicon photonics: three ways to make the light, side by side.
const S4_B: &[Beat] = &[
    Beat::new("EML: the single-mode workhorse", BEAT_MS)
        .note(
            "Three ways to make the light sit side by side. The EML comes first: an InP chip whose light leaves from its end. It is the workhorse of single-mode modules (DR, FR): fast and clean, made in small InP fabs.",
            "Three parts on a grey bench: the EML at the left, a VCSEL in the middle with its beam going up, and a silicon-photonics chip at the right. The view moves in on the EML, its glowing stripe and the cone leaving its end.",
        )
        .detail(
            "Fast and clean, but made in small fabs.",
            &["EML: InP, edge-emitting", "Single-mode DR and FR modules", "Made in small InP fabs"],
        ),
    Beat::new("VCSEL: light from the top", BEAT_MS)
        .note(
            "A VCSEL (vertical-cavity laser) sends its light straight up out of the chip's surface, between two stacks of mirror layers. Because the light leaves the surface, whole wafers can be tested before they are cut, which makes VCSELs cheap and low power. But they are multimode only, at 850 nm, for links up to about 100 m.",
            "The VCSEL cut in half: the striped layers are its mirror stacks (DBR) above and below; the thin glowing layer between them is where light is made, squeezed through a small oxide aperture. A gold ring sits on top and an orange cone of light rises out of it.",
        )
        .detail(
            "Cheap and low power, but only for short links.",
            &["850 nm, multimode", "Up to about 100 m", "Whole wafers can be tested"],
        ),
    Beat::new("silicon photonics: InP light, silicon circuits", BEAT_MS)
        .note(
            "Silicon photonics builds the modulator, splitters and waveguides in a silicon fab, so it scales with silicon manufacturing; it is what co-packaged optics use. Silicon can't make light, so a separate InP CW laser feeds it steady light, and a grating coupler sends the result up into a fibre.",
            "Seen from above: the small InP laser block at the left edge glows into a white waveguide that splits around gold electrodes and joins again, then reaches the grating coupler under the tilted fibre at the right. Dots of light run along both paths.",
        )
        .detail(
            "Scales like silicon, but still needs an InP laser.",
            &["CW LASER (InP) + silicon modulator", "Built in a silicon fab", "Used by co-packaged optics"],
        ),
];

/// 5 how a Mach-Zehnder modulator works.
const S5_B: &[Beat] = &[
    Beat::new("the light splits into two arms", BEAT_MS)
        .note(
            "A Mach-Zehnder modulator is a waveguide that splits into two arms and joins again. Light from the CW laser divides equally between the arms, and electrodes run alongside each one.",
            "A silicon chip from above: the light enters from the small laser at the left, the glowing waveguide splits into an upper and a lower arm, gold electrode strips run beside them, and the arms join again at the right. Dots of light travel both ways round.",
        )
        .detail(
            "Two equal halves of the same light.",
            &["Splitter: 50/50 into two arms", "Electrodes along each arm"],
        ),
    Beat::new("in phase, the halves add: bright", BEAT_MS)
        .note(
            "Light is a wave. With no voltage, the two halves arrive at the join in step, crest with crest, so they add up to full brightness at the output.",
            "Glowing waves lie on each arm, crests lined up. After the join a single wave twice as tall runs on to the output, which glows bright.",
        )
        .detail(
            "In phase: full brightness.",
            &["Waves in step add up"],
        ),
    Beat::new("out of phase they cancel; in between, the middle levels", BEAT_MS)
        .note(
            "A voltage on the electrodes slows the light in one arm slightly, shifting its wave. Half a wave out of step, the halves cancel and the output goes dark; anything between gives the middle PAM4 levels. Mach-Zehnder modulators are larger than ring modulators but tolerant of temperature.",
            "The centre electrode glows pink. The lower arm's wave keeps its place while the upper arm's wave shifts, and the output wave shrinks and grows through four sizes, down to a flat line when they cancel.",
        )
        .detail(
            "The phase shift sets the level.",
            &["Half a wave out: dark", "In between: middle PAM4 levels", "Bigger than rings, tolerant of temperature"],
        ),
];

/// 6 200G per lane.
const S6_B: &[Beat] = &[
    Beat::new("1.6T: eight lanes of 200G", BEAT_MS)
        .note(
            "A 1.6T module runs eight lanes at 200G each. Each lane has its own light source, here an EML, and its own fibre.",
            "From above: eight EML chips side by side on one submount, each sending a cone of light into its own glowing fibre, which run off to the right over a silicon groove block.",
        )
        .detail(
            "More speed per lane means fewer lanes for the same total.",
            &["1.6T = 8 lanes x 200G"],
        ),
    Beat::new("200G packs twice the symbols", BEAT_MS)
        .note(
            "Going from 100G to 200G per lane keeps the four PAM4 levels but sends symbols twice as fast. In the same window of time, a 200G lane carries twice as many symbols as a 100G lane.",
            "A scope screen. A cyan line sweeps left to right while two orange traces draw: the upper one (100G) with eight symbols, the lower one (200G) with sixteen in the same width.",
        )
        .detail(
            "Twice the symbols in the same time.",
            &["Same four levels, twice the rate"],
        ),
    Beat::new("the eye gets half as wide", BEAT_MS)
        .note(
            "Each symbol now has half the time, so the eye the receiver reads is half as wide and the light has to switch twice as fast. That needs EMLs and silicon modulators with roughly twice the bandwidth of 100G parts. Silicon photonics can reach 200G per lane, but it still needs an InP laser to supply the light.",
            "Two eye diagrams on the screen: the wide 100G eye on the left and the 200G eye on the right, half as wide with steeper crossings. Cyan ovals mark the open eyes; blue dots mark where the receiver reads.",
        )
        .detail(
            "Faster parts, same InP supply.",
            &["~2x the bandwidth of 100G parts", "Silicon photonics can reach 200G", "Still needs an InP laser"],
        ),
];

/// 7 the laser shortage.
const S7_B: &[Beat] = &[
    Beat::new("EML capacity is locked up", BEAT_MS)
        .note(
            "TrendForce reported in December 2025 that NVIDIA had locked up capacity at key EML suppliers, pushing lead times beyond 2027 and creating a worldwide shortage. EMLs come off small InP wafers like this one.",
            "An InP wafer covered in a grid of EML dies, some of them glowing gold: the capacity that has been reserved. One finished EML chip sits on a tray beside it.",
        )
        .detail(
            "A small supply base with a very large buyer.",
            &["TrendForce, Dec 2025", "Lead times beyond 2027", "A worldwide EML shortage"],
        ),
    Beat::new("the alternative: CW laser plus silicon", BEAT_MS)
        .note(
            "Cloud providers moved to CW laser plus silicon-modulator designs as the main alternative. That shifts demand to InP CW lasers rather than removing it: the steady light still has to come from an InP chip.",
            "A silicon-photonics chip with its glowing waveguides and gold modulator electrodes. The small laser block at its left edge, the InP CW laser, is wrapped in a gold glow.",
        )
        .detail(
            "Demand moves to a different InP part.",
            &["Main alternative: CW laser + silicon modulator", "Shifts demand to InP CW lasers"],
        ),
    Beat::new("upstream: indium", BEAT_MS)
        .note(
            "Upstream of every InP laser is indium, the In in InP. One report says China produces about 70% of the world's indium.",
            "A silver bar of indium on a tray, and a pie chart beside it: the orange slice, about 70%, is China; the grey slice is the rest of the world.",
        )
        .detail(
            "The raw material is concentrated too.",
            &["China: ~70% of indium (one report)"],
        ),
];

/// 8 who makes it.
const S8_B: &[Beat] = &[
    Beat::new("EML makers", BEAT_MS)
        .note(
            "EMLs come from a handful of companies: Lumentum (LITE), Coherent (COHR), Mitsubishi Electric, Sumitomo and Broadcom (AVGO).",
            "Five EML chips in the pockets of a dark tray, each tagged with a maker, their stripes lighting one by one.",
        )
        .detail(
            "Few suppliers for the single-mode workhorse.",
            &["Lumentum, Coherent, Mitsubishi Electric", "Sumitomo, Broadcom"],
        ),
    Beat::new("VCSEL makers", BEAT_MS)
        .note(
            "VCSELs, for short multimode links, come from Coherent, Broadcom and Lumentum.",
            "Three small VCSEL dies, each with a row of four round mesas glowing at the top and gold pads in front, each tagged with a maker. Cones of light rise from the mesas.",
        )
        .detail(
            "The same names show up again.",
            &["Coherent, Broadcom, Lumentum"],
        ),
    Beat::new("silicon photonics: designers and foundries", BEAT_MS)
        .note(
            "Silicon photonics is designed by Intel, Cisco, Broadcom, Marvell and others, with wafers from foundries such as TSMC, GlobalFoundries and Tower (TSEM).",
            "A large silicon wafer covered in pale photonic dies, tagged with the designers and the foundries.",
        )
        .detail(
            "Silicon photonics brings in silicon's supply chain.",
            &["Intel, Cisco, Broadcom, Marvell", "TSMC, GlobalFoundries, Tower (TSEM)"],
        ),
];

/// 9 chokepoints and risks.
const S9_B: &[Beat] = &[
    Beat::new("EML capacity is small and slow to add", BEAT_MS)
        .note(
            "EMLs are made in small InP fabs, on wafers far smaller than silicon's. That capacity is small and slow to add, and lead times run past 2027.",
            "A small InP wafer, its rim glowing gold, lying on a 300 mm silicon wafer for scale.",
        )
        .detail(
            "Capacity can't jump to meet demand.",
            &["Lead times past 2027", "Small InP fabs"],
        ),
    Beat::new("every route still needs InP lasers", BEAT_MS)
        .note(
            "Switching routes does not escape the chokepoint. An EML is InP; the CW laser that feeds a silicon modulator is InP too. Every single-mode route still needs INDIUM PHOSPHIDE lasers.",
            "An EML chip on the left and a silicon-photonics chip on the right, on one bench. The whole EML and the silicon chip's small laser block both glow gold: the InP parts.",
        )
        .detail(
            "InP is the common dependency.",
            &["EML: InP", "CW laser for silicon photonics: InP"],
        ),
    Beat::new("lasers fail more than electronics", BEAT_MS)
        .note(
            "Lasers fail more often than electronics. In a pluggable module a failed laser means swapping one module; when the lasers sit inside the switch package, as in co-packaged optics, a failure is much harder to fix (see CPO).",
            "A switch package from above: the grey switch ASIC in the middle, eight blue optical engines around it with glowing lasers and fibres. One laser goes out and turns red.",
        )
        .detail(
            "Reliability matters most inside the package.",
            &["Lasers fail more than electronics", "Inside the switch package: hard to fix"],
        ),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_laser_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_laser_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_laser_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_laser_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_laser_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_laser_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_laser_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_laser_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_laser_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
