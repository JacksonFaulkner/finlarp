// CPO: numbered sections 1-9, one per heading of diagrams_pages/FIB_CPO.txt, from the Blender scenes in
// tools/pbr3d/blender/fiber_cpo_sections.py (GLBs in tools/pbr3d/assets/fiber_cpo_section_<n>.glb).
// Three beats per section, 8 s each.

use super::super::super::blender::{Cell, page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static CELL_1: Cell = std::sync::OnceLock::new();
static CELL_2: Cell = std::sync::OnceLock::new();
static CELL_3: Cell = std::sync::OnceLock::new();
static CELL_4: Cell = std::sync::OnceLock::new();
static CELL_5: Cell = std::sync::OnceLock::new();
static CELL_6: Cell = std::sync::OnceLock::new();
static CELL_7: Cell = std::sync::OnceLock::new();
static CELL_8: Cell = std::sync::OnceLock::new();
static CELL_9: Cell = std::sync::OnceLock::new();

/// 1. What happens: the optics move onto the switch package.
const S1_B: &[Beat] = &[
    Beat::new("today: long copper to pluggables at the panel", BEAT_MS)
        .note(
            "In a normal switch the switch chip drives electrical signals across the board to pluggable modules at the front panel, tens of centimetres away. Each module needs a DSP to clean up the signal before its optics turn it into light.",
            "At the back of the board: the lidded switch package, thin copper traces running across the green board with cyan dots on them, and four grey modules in cages at the steel panel. The front module is cut open: green PCB, dark DSP chip, steel laser and photodiode cans.",
        )
        .detail(
            "The distance is the problem CPO removes.",
            &["Chip to panel: tens of cm of trace", "A DSP in every module"],
        ),
    Beat::new("CPO: optical engines on the package", BEAT_MS)
        .note(
            "Co-packaged optics put optical engines on the switch package itself, millimetres from the chip. Each engine is a silicon-photonics chip with its driver chip on top. The signal turns into light right there and leaves the package in fibre.",
            "At the front: the CPO package, a grey-blue switch chip ringed by eight lavender engines, and two aqua fibre cables running straight to the panel. Orange-white light pulses travel along them.",
        )
        .detail(
            "Millimetres of copper instead of tens of centimetres.",
            &["Engine = photonic chip + electronic chip", "Light leaves the package in fibre"],
        ),
    Beat::new("the laser stays at the panel", BEAT_MS)
        .note(
            "The engines don't make their own light. An external laser in a pluggable box at the front panel supplies steady light, carried to the engines by fibre. The engines only switch that light on and off with the data.",
            "The finned dark module through the steel panel is the external laser. Red-pink fibres glow with its steady light all the way back to the package.",
        )
        .detail(
            "Steady light in, data light out.",
            &["External laser: pluggable, at the panel", "Feeds the engines through fibre"],
        ),
];

/// 2. The parts.
const S2_B: &[Beat] = &[
    Beat::new("co-packaged optics: engines around the chip", BEAT_MS)
        .note(
            "Co-packaged optics means optical engines on the same package as the switch chip. Here eight engines sit around the chip, two per side, on one substrate. Fibre runs from each engine to a connector on the board.",
            "The grey-blue switch chip in the middle of the brown-grey substrate, the eight lavender engines around it, and aqua fibre connectors on the green board. Every engine is busy: cyan electrons cross from the chip and orange light beads leave down all eight fibre arrays.",
        )
        .detail(
            "Watts per port is the reason to do this.",
            &["Power per port: watts per 1.6T port", "The main reason for CPO"],
        ),
    Beat::new("the optical engine up close", BEAT_MS)
        .note(
            "An optical engine is a photonic chip (modulators and photodiodes) with an electronic chip stacked on it. The modulators are micro-rings: ring-shaped waveguides a few microns across, each tuned to one wavelength. Photodiodes catch incoming light on the receive lanes.",
            "The lavender photonic chip with white waveguides, the laser bus glowing pink: the gold rings flash as micro-ring modulators, the photodiode pads light up as received light lands on them, and the dark block on the inner end is the electronic chip.",
        )
        .detail(
            "TSMC's COUPE process stacks the electronic chip on the photonic chip.",
            &["Micro-ring: a few microns across", "COUPE: TSMC's stacking process"],
        ),
    Beat::new("external laser and front panel", BEAT_MS)
        .note(
            "The front panel is where pluggable modules sit today. With CPO it holds fibre ports and the external lasers instead. Keeping the laser there helps serviceability: a pluggable part is easy to swap, a part soldered into the package is not.",
            "The steel front panel with a fibre port (dark adapter) and the finned external laser module through it; red-pink laser fibres run back toward the package.",
        )
        .detail(
            "Serviceability: easy for a pluggable, hard for a package.",
            &["Panel: external lasers + fibre ports", "Engines can't be swapped like modules"],
        ),
];

/// 3. A bit's path with CPO, in order.
const S3_B: &[Beat] = &[
    Beat::new("1: SerDes drives a few mm of package wiring", BEAT_MS)
        .note(
            "A bit leaving the switch starts at the chip's SerDes, the circuits along its edge that drive data off the chip. With CPO they only have to drive a few millimetres of wiring in the package to reach the engine's electronic chip.",
            "From above: the gold SerDes band on the chip's edge, short copper traces across the gap, and cyan dots running along them into the dark electronic chip.",
        )
        .detail(
            "Steps 1 of 5.",
            &["A few mm of package wiring", "No DSP on the way"],
        ),
    Beat::new("2-3: the electronic chip drives a ring, which imprints the data", BEAT_MS)
        .note(
            "The engine's electronic chip drives a micro-ring modulator. Steady light from the external laser runs past the ring; as the voltage swings with the data, the ring lets the light through or holds it back, imprinting the bits onto the light.",
            "Red-pink laser light glows along the outer waveguides and the bus by the dark electronic chip. The gold rings flash as they are driven, and orange-white pulses leave each ring toward the fibre array.",
        )
        .detail(
            "Steps 2 and 3 of 5.",
            &["Ring modulates laser light", "Laser light comes in by fibre"],
        ),
    Beat::new("4-5: out in fibre, back in to the photodiodes", BEAT_MS)
        .note(
            "The modulated light leaves the package in fibre to the front panel. Traffic coming the other way arrives as light on other fibres; germanium photodiodes in the engine turn it into current, and TIAs in the electronic chip turn that back into electrical lanes for the switch chip.",
            "Orange-white pulses run out along the lower fibres through the connector toward the panel, and in along the upper fibres to the photodiode pads, which light up.",
        )
        .detail(
            "Steps 4 and 5 of 5.",
            &["Out: fibre to the front panel", "In: germanium photodiodes + TIAs"],
        ),
];

/// 4. Why: the copper is the problem.
const S4_B: &[Beat] = &[
    Beat::new("200G over a long trace needs a DSP", BEAT_MS)
        .note(
            "At 200G per lane, a long trace from the switch chip to the front panel loses so much signal that every pluggable module needs a DSP to recover it. Driving the trace and running all those DSPs costs a lot of power.",
            "The pluggable switch: cyan dots crawl along the long copper traces from the lidded package to the caged modules; the cut-open module shows its dark DSP chip.",
        )
        .detail(
            "The long electrical path forces a DSP per module.",
            &["200G per lane", "A DSP in every module"],
        ),
    Beat::new("millimetres let the engine drive the optics", BEAT_MS)
        .note(
            "Shortening the electrical path to millimetres keeps the signal clean enough that the engine can drive the optics directly, with no DSP in between.",
            "Close on the CPO package: cyan dots cross a few millimetres of copper between the gold SerDes edge and the dark electronic chip on the lavender engine.",
        )
        .detail(
            "Less copper, less power.",
            &["Millimetres instead of tens of cm", "No DSP between chip and optics"],
        ),
    Beat::new("the payoff: power per port", BEAT_MS)
        .note(
            "The saving shows up in power per port. NVIDIA says its photonics switches cut power 3.5x versus pluggable transceivers. One report puts a 1.6T port at about 9 W with CPO instead of about 25 W with pluggables.",
            "Both switches in one frame: the pluggable one at the back with its long traces and modules, the CPO one at the front with fibre to the panel.",
        )
        .detail(
            "Power per port is the main reason for CPO.",
            &["NVIDIA: 3.5x lower power (claimed)", "1.6T port: ~9 W vs ~25 W (one report)"],
        ),
];

/// 5. Inside the optical engine.
const S5_B: &[Beat] = &[
    Beat::new("an electronic chip stacked on a photonic one", BEAT_MS)
        .note(
            "NVIDIA's engines are made on TSMC's COUPE process, which stacks an electronic chip on a photonic chip. The photonic chip carries the light; the electronic chip on top drives the modulators and amplifies what the photodiodes receive.",
            "The engine cut open down one lane: the dark electronic chip on a row of silver microbumps, copper vias running down through the lavender photonic chip, a thin dark buried-oxide layer and a white waveguide core. Cyan electrons climb from the substrate up into the electronic chip while orange light runs out along the waveguide.",
        )
        .detail(
            "Stacking keeps the driver right over the optics.",
            &["TSMC COUPE", "Electronic chip on photonic chip"],
        ),
    Beat::new("200G micro-ring modulators", BEAT_MS)
        .note(
            "The modulators are 200 Gb/s micro-rings. A ring a few microns across couples light only at its resonant wavelength. A voltage shifts that resonance, turning the light passing by up or down, and that is how the data gets onto the light.",
            "Red-pink laser light runs along the bus and waveguides. The gold rings flash as the electronic chip drives them, and pulses leave toward the fibre array.",
        )
        .detail(
            "Tiny and efficient.",
            &["200 Gb/s per micro-ring", "A few microns across"],
        ),
    Beat::new("rings are sensitive to temperature", BEAT_MS)
        .note(
            "Rings are tiny and efficient but sensitive to temperature: warm one up and its resonance drifts off the laser's wavelength. So each ring needs heater control that holds it on tune.",
            "A pulsing red-orange glow over the rings; the copper loop around each gold ring is its heater.",
        )
        .detail(
            "Every ring needs active tuning.",
            &["Resonance drifts with heat", "A heater per ring keeps it tuned"],
        ),
];

/// 6. Lasers stay pluggable.
const S6_B: &[Beat] = &[
    Beat::new("the laser lives at the panel", BEAT_MS)
        .note(
            "Lasers fail more often than silicon and run best cool, so CPO keeps them away from the hot switch package. They sit out at the front panel in external laser modules and send their light to the engines over fibre.",
            "The finned dark external laser module through the steel panel; red-pink fibres carry its light round to the cable connector and on toward the engine.",
        )
        .detail(
            "Away from the heat, where it can be reached.",
            &["Lasers fail more often than silicon", "And run best cool"],
        ),
    Beat::new("swapped like a pluggable", BEAT_MS)
        .note(
            "Because the laser is a pluggable module, a failed one can be pulled from the panel and replaced, while the engines on the package stay where they are.",
            "The laser module slides out of the panel and back in. The package and its engines don't move.",
        )
        .detail(
            "Keeps the part most likely to fail serviceable.",
            &["External laser: a pluggable module", "Engines stay on the package"],
        ),
    Beat::new("fewer lasers: 2 per 1.6T link, not 8", BEAT_MS)
        .note(
            "One shared laser source can feed several modulators, so fewer lasers are needed. Coverage of NVIDIA's Hot Chips 2025 talk says a 1.6 Tb/s link needs two lasers instead of eight, a 4x reduction.",
            "The module's cover lifts off: inside, two dark laser chips with glowing red facets send light into the two red-pink fibres.",
        )
        .detail(
            "Fewer lasers, fewer failures.",
            &["2 lasers instead of 8 per 1.6 Tb/s", "4x fewer (Hot Chips 2025 coverage)"],
        ),
];

/// 7. The switches.
const S7_B: &[Beat] = &[
    Beat::new("NVIDIA Spectrum-X and Quantum-X Photonics", BEAT_MS)
        .note(
            "NVIDIA's Spectrum-X (Ethernet) and Quantum-X (InfiniBand) Photonics switches put the optical engines on the switch package. They are scheduled from the second half of 2026.",
            "A CPO switch package: the grey-blue switch chip with eight lavender engines around it on the substrate, fibre cables running to the panel.",
        )
        .detail(
            "Scheduled from 2H 2026.",
            &["Spectrum-X Photonics (Ethernet)", "Quantum-X Photonics (InfiniBand)"],
        ),
    Beat::new("a front panel of fibre ports", BEAT_MS)
        .note(
            "The front panel carries fibre ports instead of module cages. Configurations include 128 ports of 800 Gb/s or 512 ports of 200 Gb/s.",
            "Two rows of dark fibre ports with aqua inserts along the steel panel; light pulses run from the engines down the cables to it.",
        )
        .detail(
            "Same total, split different ways.",
            &["128 x 800 Gb/s", "or 512 x 200 Gb/s"],
        ),
    Beat::new("~100 Tb/s per switch; Broadcom too", BEAT_MS)
        .note(
            "Either way that is about 100 Tb/s of switching. NVIDIA's Quantum-X Photonics switch is liquid-cooled. Broadcom also builds CPO versions of its Tomahawk switch chips.",
            "A steel cold plate over the package with its front quadrant cut away to show the microchannel fins over the die; blue coolant beads flow in through the inlet pipe and along the channels, and warm orange beads leave through the outlet.",
        )
        .detail(
            "Two switch makers so far.",
            &["~100 Tb/s in total", "Broadcom: CPO Tomahawk versions"],
        ),
];

/// 8. Who makes it.
const S8_B: &[Beat] = &[
    Beat::new("switch design and the chips", BEAT_MS)
        .note(
            "NVIDIA (NVDA) and Broadcom (AVGO) design the CPO switches. TSMC (TSM) makes both the photonic and electronic chips in the engines and packages them with the switch chip.",
            "Cyan highlights on the switch chip and on all eight engines around it.",
        )
        .detail(
            "Design: NVDA, AVGO. Chips and packaging: TSM.",
            &["NVIDIA, Broadcom: switch design", "TSMC: chips + packaging"],
        ),
    Beat::new("the external lasers", BEAT_MS)
        .note(
            "Laser makers such as Lumentum (LITE) and Coherent (COHR) supply the external lasers that sit at the front panel.",
            "A cyan highlight around the finned external laser module in the panel.",
        )
        .detail(
            "Laser makers: LITE, COHR.",
            &["Lumentum (LITE)", "Coherent (COHR)"],
        ),
    Beat::new("fibre and connectors", BEAT_MS)
        .note(
            "Corning (GLW) and others supply the fibre and connectors: the cable from the package to the panel, the panel ports and the cable out.",
            "A cyan highlight on the passive cable connector at the package edge; outside the panel, orange-white light beads run out along the aqua fibre cable.",
        )
        .detail(
            "Fibre and connectors: GLW and others.",
            &["Corning (GLW)", "Fibre + connectors"],
        ),
];

/// 9. Chokepoints and risks.
const S9_B: &[Beat] = &[
    Beat::new("serviceability: a failed engine", BEAT_MS)
        .note(
            "With pluggables a failed transceiver is one module out of the panel. With CPO the engine is part of the switch package, so a failed engine means replacing the whole switch board, not one module.",
            "One engine pulses red and sends no light; the other seven keep firing orange beads down their fibres. Because the engine is bonded to the package, fixing it means swapping the whole switch board.",
        )
        .detail(
            "The biggest operational risk.",
            &["Failed engine = whole board", "Pluggable = one module"],
        ),
    Beat::new("attaching fibre at scale", BEAT_MS)
        .note(
            "Every engine needs fibres aligned and fixed to its photonic chip with low loss. Doing that at scale, on a big expensive package, is a new manufacturing step.",
            "Close on one engine's fibre array, outlined in cyan: the grey V-groove block, the clear lid and the fibres in their grooves.",
        )
        .detail(
            "A new step in volume manufacturing.",
            &["Fibre attach to the package", "Low loss, at scale"],
        ),
    Beat::new("optics tied to one vendor", BEAT_MS)
        .note(
            "Pluggables are an open market: any vendor's module fits the cage. CPO ties the optics to one switch vendor's package instead.",
            "The whole package outlined in cyan, beside the front panel where interchangeable modules would otherwise sit.",
        )
        .detail(
            "Less choice for buyers.",
            &["Optics tied to the switch package", "Not an open module market"],
        ),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &CELL_1,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_cpo_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &CELL_2,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_cpo_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &CELL_3,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_cpo_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &CELL_4,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_cpo_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &CELL_5,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_cpo_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &CELL_6,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_cpo_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &CELL_7,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_cpo_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &CELL_8,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_cpo_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &CELL_9,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_cpo_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
