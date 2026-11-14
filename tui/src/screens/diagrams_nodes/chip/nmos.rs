// CHIP tab, NMOS: the node's overview is the whole-chip scene (tools/pbr3d/blender/chip_kit.py)
// with the camera zooming in on this part (tools/pbr3d/blender/chip_nmos.py). Six beats: the
// whole chip, in on the NMOS with the gate low, the gate rising and the channel forming, the
// electrons flowing source to drain, the gate falling, and back out. Zoom-ins a-e and sections
// 1-10 are their own Blender scenes in the same template.
//
// Sources: CHIP_NMOS.txt section 10 (anandtech.com/show/21310; Banerjee, UCSB ECE225 Lecture 5;
// semiengineering.com 18A coverage); textbook figures are marked as such.

use super::super::blender::{page, Cell, Page, BEAT_MS};
use super::super::Node;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("whole chip: one NMOS, the pull-down switch, picked out in cyan", BEAT_MS)
        .note(
            "The whole chip in cut-away: silicon at the bottom, copper wiring above, package bumps on top. One transistor, the NMOS of the inverter, is picked out in cyan.",
            "a cyan box around the NMOS at the silicon surface, with the wiring tiers and bumps above it",
        )
        .detail(
            "Every switch in the chip is an NMOS or a PMOS, and billions of them make a modern GPU.",
            &["NVIDIA B200: 208 billion transistors (anandtech.com/show/21310)", "AMD MI300X: 153 billion (tweaktown.com/news/94342)"],
        ),
    Beat::new("off: gate low, no channel between the two n+ islands", BEAT_MS)
        .note(
            "Zoomed in: two n+ islands, the source and the drain, sit in p-type silicon. With the gate at 0 V there is no channel between them, so no current flows.",
            "the blue n+ source and drain blocks in the tan silicon, the grey gate low, and no glow under it",
        )
        .detail(
            "In the off state the junctions block current; only leakage flows.",
            &["n+ source/drain about 1e20-1e21 /cm3 (textbook)", "p-well about 1e15-1e18 /cm3 (textbook)"],
        ),
    Beat::new("gate up: the gate rises and a channel forms under it", BEAT_MS)
        .note(
            "The gate voltage rises above the threshold. The gate draws no current; its field pulls electrons to the surface, and a thin n-type channel joins source to drain.",
            "the gate glowing amber, then a cyan sheet on the silicon surface between the n+ islands",
        )
        .detail(
            "The threshold voltage sets when the switch turns on.",
            &["Inversion above Vt (textbook)", "Gate draws no current: only its field reaches the silicon (CHIP_NMOS.txt, section 1)"],
        ),
    Beat::new("flow: electrons run from the source, through the channel, to the drain", BEAT_MS)
        .note(
            "With the channel open, electrons leave the grounded source, cross the channel and climb the drain contact. Conventional current runs the other way, from drain to source.",
            "cyan dots running from the left n+ block along the surface, across the channel and up the right contact",
        )
        .detail(
            "Electrons carry the current: they move about 2-3 times faster than holes, so an NMOS drives more current per width than a PMOS.",
            &["Electron mobility about 2-3x that of holes (textbook)", "Saturation velocity about 1e7 cm/s (textbook)"],
        ),
    Beat::new("gate down: the gate falls, the channel closes and the flow stops", BEAT_MS)
        .note(
            "The gate drops back to 0 V. The glow goes out, the channel empties and the electrons stop; a small leakage current remains.",
            "the amber glow and the cyan sheet go out together, and no dots are left on the path",
        )
        .detail(
            "The switch cannot turn off perfectly: below threshold, leakage falls only about 10x per 60-100 mV.",
            &["S >= 60 mV/decade at 300 K (textbook)", "Real S about 70-90 mV/dec (CHIP_NMOS.txt, section 4)"],
        ),
    Beat::new("whole chip again: one switch of billions, wired by contacts and metal", BEAT_MS)
        .note(
            "Back out to the whole chip. The NMOS is one of billions of switches, wired to its neighbours by tungsten contacts and copper metal.",
            "the chip in cut-away again, the cyan box around the NMOS fading back in",
        )
        .detail(
            "The count grows with each node, and every switch is built the same way.",
            &["NVIDIA H100/H200: 80 billion transistors (anandtech.com/show/21310)", "Apple M4: 28 billion (en.wikipedia.org/wiki/Apple_M4)"],
        ),
];

// ---- zoom-ins a-e: the gate stack, threshold, saturation, DIBL, dopants -----------------------

const ZA_BEATS: &[Beat] = &[
    Beat::new("the gate stack, cut open: metal on high-k over the silicon", BEAT_MS)
        .note(
            "Cut through the gate: a metal gate on a thin high-k dielectric over the silicon. The gate is the switch's input.",
            "the grey metal gate block on a pale high-k strip, the tan silicon below, and the blue n+ blocks either side",
        )
        .detail(
            "The gate and its thin dielectric set how strongly the field reaches the silicon.",
            &["Metal gate + high-k (HfO2) + thin SiO2 (CHIP_NMOS.txt, section 2)", "GATE STACK about 1 nm EOT class (CHIP_NMOS.txt, section 2)"],
        ),
    Beat::new("gate voltage on: the field reaches through the oxide", BEAT_MS)
        .note(
            "A gate voltage sets up a field across the dielectric that controls the silicon below. No current flows into the gate, only its field.",
            "the gate glowing amber, and two pink field lines running down from the gate into the silicon",
        )
        .detail(
            "The gate's field is the only thing that reaches the silicon.",
            &["Gate draws no current: only its field reaches the silicon (CHIP_NMOS.txt, section 1)", "Capacitive control (textbook)"],
        ),
    Beat::new("the channel: electrons gather at the surface", BEAT_MS)
        .note(
            "Above the threshold the field pulls electrons up to the surface, and a thin n-type layer joins source to drain.",
            "a cyan sheet on the silicon surface between the n+ blocks, under the amber gate",
        )
        .detail(
            "The threshold voltage sets when this layer forms.",
            &["INVERSION: above the threshold voltage, electrons gather into a channel (CHIP_NMOS.txt, section 3)"],
        ),
    Beat::new("high-k: thick but electrically thin", BEAT_MS)
        .note(
            "High-k material lets the layer stay physically thick enough to stop tunnelling while acting electrically thin. The gate stays lit and the channel is still on.",
            "the pale high-k strip brightened, the amber gate and the cyan channel both still lit",
        )
        .detail(
            "More control from the gate, and less leakage through the dielectric.",
            &["High-k replaced SiO2 gates (textbook)", "Gate stack: high-k over thin SiO2 (CHIP_NMOS.txt, section 2)"],
        ),
];

const ZB_BEATS: &[Beat] = &[
    Beat::new("below threshold: leakage only", BEAT_MS)
        .note(
            "Below the threshold a weak current still flows, rising exponentially with gate voltage. The gate is dark and a few faint dots cross under the surface.",
            "faint dots crossing under the surface between the n+ blocks, the gate dark",
        )
        .detail(
            "This is the off-state leakage. It sets how far the threshold can be lowered.",
            &["S >= 60 mV/decade at 300 K (CHIP_NMOS.txt, section 4)", "Real S about 70-90 mV/decade (CHIP_NMOS.txt, section 4)"],
        ),
    Beat::new("threshold: inversion starts and the channel forms", BEAT_MS)
        .note(
            "At the threshold voltage strong inversion starts: the gate glows, the cyan sheet forms on the surface and the current climbs steeply.",
            "the amber gate and the cyan sheet forming on the silicon surface; no dots yet",
        )
        .detail(
            "The threshold is where the switch turns on.",
            &["Threshold: the inversion layer forms (CHIP_NMOS.txt, section 4)"],
        ),
    Beat::new("above threshold: full current", BEAT_MS)
        .note(
            "Well above threshold the current grows more slowly, because the electrons reach their velocity limit. A dense stream of dots runs source to drain.",
            "bright dots streaming along the surface from the source to the drain, the gate and the sheet lit",
        )
        .detail(
            "Each 60-100 mV of threshold reduction gives about 10x more off-state leakage, so Vt cannot be scaled freely.",
            &["Rule: about 10x more off-state leakage per 60-100 mV (CHIP_NMOS.txt, section 4)"],
        ),
];

const ZC_BEATS: &[Beat] = &[
    Beat::new("low drain voltage: an even channel", BEAT_MS)
        .note(
            "With a small drain voltage the channel is the same thickness end to end, and the current rises with the drain voltage.",
            "a full cyan sheet between the n+ blocks under the amber gate, with dots flowing evenly",
        )
        .detail(
            "At a small drain voltage the channel acts like a resistor.",
            &["Linear region at small drain voltage (CHIP_NMOS.txt, section 3)"],
        ),
    Beat::new("the drain end thins: the drain weakens the gate's pull", BEAT_MS)
        .note(
            "The drain voltage reduces the gate's pull near the drain, so the channel thins there and the sheet tapers towards the drain.",
            "the cyan sheet shortened on the drain side, the dots still flowing",
        )
        .detail(
            "This is where pinch-off begins: saturation starts when VD > VG - Vt.",
            &["Saturation: VD > VG - Vt (CHIP_NMOS.txt, section 3)"],
        ),
    Beat::new("pinch-off at the drain: current levels out", BEAT_MS)
        .note(
            "At high drain voltage the channel stops short of the drain. The electrons race across the gap, and current barely rises with more drain voltage.",
            "the sheet stopping short of the drain, the dots running across the gap",
        )
        .detail(
            "Digital switching happens in saturation, where the current is nearly flat in drain voltage.",
            &["Current levels out in saturation (CHIP_NMOS.txt, section 3)"],
        ),
];

const ZD_BEATS: &[Beat] = &[
    Beat::new("a long gate: the gate owns the barrier", BEAT_MS)
        .note(
            "In a long device the gate alone sets the barrier between source and drain. The gate glows, the channel is even, and nothing leaks.",
            "the amber gate glowing over a cyan sheet, with no dots under the surface",
        )
        .detail(
            "With a long gate the threshold is steady.",
            &["Long channel: the gate sets the barrier (textbook)"],
        ),
    Beat::new("the drain field reaches the source: DIBL", BEAT_MS)
        .note(
            "In a short channel the drain's field reaches the source side and lowers the barrier: drain-induced barrier lowering (DIBL). Three pink field lines run from the drain toward the channel.",
            "three pink field lines running from the drain toward the channel, and the channel still lit",
        )
        .detail(
            "The threshold falls as the channel shrinks, and the falling threshold lets leakage start.",
            &["DIBL: the drain lowers the source barrier and Vt falls with drain voltage (CHIP_NMOS.txt, section 5)", "Vt roll-off as the channel shrinks (textbook)"],
        ),
    Beat::new("higher drain voltage: more leakage", BEAT_MS)
        .note(
            "A higher drain voltage lowers the barrier further, so more dots cross under the surface while the gate is dark.",
            "more faint dots crossing under the surface, and the gate dark",
        )
        .detail(
            "Wrapping the gate around the channel fights this, which is what FinFET and GAA do.",
            &["Leakage under the channel (CHIP_NMOS.txt, section 5)", "FinFET and GAA gates surround the channel (CHIP_NMOS.txt, section 5)"],
        ),
];

const ZE_BEATS: &[Beat] = &[
    Beat::new("dopants in the source and drain: arsenic or phosphorus", BEAT_MS)
        .note(
            "Arsenic or phosphorus atoms make the source and drain n-type. Arsenic diffuses slowly and gives sharp junctions; phosphorus activates better but spreads deeper.",
            "the n+ source and drain glowing gold, with dopant atoms in their faces",
        )
        .detail(
            "The two dopants trade activation against depth.",
            &["N+ SOURCE: arsenic or phosphorus, about 1e20-1e21 /cm3 (CHIP_NMOS.txt, section 2)", "Arsenic shallow and abrupt; phosphorus deeper (CHIP_NMOS.txt, section 6)"],
        ),
    Beat::new("Si:P epitaxy and halo pockets", BEAT_MS)
        .note(
            "Phosphorus-doped silicon grown in place reaches about 1.2e21 /cm3. Halo pockets of the opposite type sit beside the channel ends and stop punch-through.",
            "the source and drain still gold, with lilac halo pockets beside the channel ends",
        )
        .detail(
            "The halos keep the depletion region from reaching through the channel.",
            &["Si:P grown in place reaches about 1.2e21 /cm3 and 0.3 mOhm.cm (CHIP_NMOS.txt, section 6)", "Halo pockets stop punch-through (CHIP_NMOS.txt, section 2)"],
        ),
    Beat::new("tensile strain: faster electrons", BEAT_MS)
        .note(
            "Si:P stretches the channel: tensile strain raises electron mobility, so the switch drives more current. The gold strain bar pulls outward along the channel and the dots flow faster.",
            "a gold strain bar pulling outward along the channel, the channel lit and the dots streaming faster",
        )
        .detail(
            "PMOS uses compressive strain instead.",
            &["Si:P stretches the channel (tensile strain), speeding electrons (CHIP_NMOS.txt, section 6)", "PMOS uses compressive strain (textbook)"],
        ),
];

// ---- sections 1-10 ----------------------------------------------------------------------------

const SEC1: &[Beat] = &[
    Beat::new("off: gate low, no channel", BEAT_MS)
        .note(
            "With the gate at 0 V the junctions block current, so the switch is off. The two blue n+ blocks sit in tan silicon with nothing joining them.",
            "the two blue n+ blocks in tan silicon, the gate dark, and no channel between them",
        )
        .detail(
            "With the gate at 0 V the switch is off.",
            &["OFF STATE: gate at 0 V; the junctions block current (CHIP_NMOS.txt, section 3)"],
        ),
    Beat::new("gate high: an electron channel forms", BEAT_MS)
        .note(
            "The gate goes high and the field pulls electrons to the surface. No current enters the gate; the field does the work.",
            "the gate glowing amber and the cyan channel on the surface between the blue blocks",
        )
        .detail(
            "Only the gate's field reaches the silicon.",
            &["Gate draws no current (CHIP_NMOS.txt, section 1)", "INVERSION above threshold (CHIP_NMOS.txt, section 3)"],
        ),
    Beat::new("current flows: electrons run source to drain", BEAT_MS)
        .note(
            "The drain voltage pulls electrons across the channel from the source. Cyan dots run along the surface from the left block to the right.",
            "cyan dots running along the surface from the left block to the right, through the channel",
        )
        .detail(
            "Electrons carry more current per width than holes, so an NMOS is the stronger switch.",
            &["Electron mobility about 2-3x that of holes (textbook)"],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("N+ SOURCE", BEAT_MS)
        .note(
            "Heavily doped n-type silicon, usually grounded. The source block is lit and the rest of the chip is dim.",
            "the source block lit cyan, the rest of the picture dimmed",
        )
        .detail(
            "Arsenic or phosphorus at about 1e20-1e21 /cm3.",
            &["N+ SOURCE: arsenic or phosphorus, about 1e20-1e21 /cm3 (CHIP_NMOS.txt, section 2)"],
        ),
    Beat::new("GATE STACK", BEAT_MS)
        .note(
            "A metal gate on a high-k dielectric over a thin SiO2 layer is the switch's input. The gate block is lit.",
            "the gate block lit cyan above the thin dielectric",
        )
        .detail(
            "About 1 nm EOT class.",
            &["GATE STACK: metal on high-k over thin SiO2, about 1 nm EOT class (CHIP_NMOS.txt, section 2)"],
        ),
    Beat::new("N+ DRAIN", BEAT_MS)
        .note(
            "The output node, tied to the load or to VDD. The drain block is lit.",
            "the drain block lit cyan",
        )
        .detail(
            "Same doping as the source.",
            &["N+ DRAIN: the output node, tied to the load or VDD (CHIP_NMOS.txt, section 2)"],
        ),
    Beat::new("P-WELL", BEAT_MS)
        .note(
            "The p-type body the device sits in; holes are the majority carrier. The well is lit in violet below and around the device.",
            "the substrate lit violet below and around the device",
        )
        .detail(
            "Boron-doped, about 1e15-1e18 /cm3.",
            &["P-WELL: boron-doped, about 1e15-1e18 /cm3 (CHIP_NMOS.txt, section 2)"],
        ),
    Beat::new("halo pockets, spacers, STI", BEAT_MS)
        .note(
            "Halo pockets beside the channel ends stop punch-through; spacers set the extension spacing; the oxide wall at the right is STI, which isolates neighbours.",
            "the violet halo pockets beside the channel ends, and an oxide wall at the right",
        )
        .detail(
            "Small parts, big effect on leakage.",
            &["Halo pockets stop punch-through; spacers set the extension spacing; STI isolates neighbours (CHIP_NMOS.txt, section 2)"],
        ),
];

const SEC3: &[Beat] = &[
    Beat::new("1. OFF STATE: gate at 0 V", BEAT_MS)
        .note(
            "The device at rest. The gate is at 0 V and the junctions block current, so nothing glows and no dots move.",
            "the device at rest with the gate dark and no glow or dots",
        )
        .detail(
            "Only leakage flows at rest.",
            &["VG = 0; the junctions block current (CHIP_NMOS.txt, section 3)"],
        ),
    Beat::new("2. DEPLETION: holes pushed away", BEAT_MS)
        .note(
            "A small gate voltage pushes the holes away from the surface, leaving a depletion region under the gate. No channel forms yet.",
            "a violet band under the gate in the silicon, where the holes have been pushed away",
        )
        .detail(
            "Depletion comes before any channel forms.",
            &["0 < VG < Vt: holes pushed away from the surface (CHIP_NMOS.txt, section 3)"],
        ),
    Beat::new("3. INVERSION: electron channel", BEAT_MS)
        .note(
            "Above the threshold, electrons gather into a channel and the switch is on. The gate glows and the cyan sheet forms on the surface.",
            "the gate glowing amber and the cyan sheet on the surface between the blocks",
        )
        .detail(
            "The switch is on once the gate is above threshold.",
            &["VG > Vt (CHIP_NMOS.txt, section 3)"],
        ),
    Beat::new("4. LINEAR, then SATURATION", BEAT_MS)
        .note(
            "The drain voltage drives the electrons: first the channel is even and the dots flow, then at high drain voltage the sheet pinches off at the drain.",
            "cyan dots flowing source to drain; the sheet full at first, then shortened at the drain end",
        )
        .detail(
            "Current levels out once the channel pinches off.",
            &["VD > VG - Vt for saturation (CHIP_NMOS.txt, section 3)"],
        ),
    Beat::new("5. TURN-OFF: channel empties", BEAT_MS)
        .note(
            "The gate drops back to 0 V. The glow and the sheet go out, and only a few faint dots remain under the surface.",
            "the gate dark, the sheet gone, and only a few faint dots under the surface",
        )
        .detail(
            "The switch cannot turn off perfectly: leakage remains below threshold.",
            &["VG -> 0 (CHIP_NMOS.txt, section 3)", "S >= 60 mV/decade at 300 K (CHIP_NMOS.txt, section 4)"],
        ),
];

const SEC4: &[Beat] = ZB_BEATS;

const SEC5: &[Beat] = &[
    Beat::new("DIBL: a short channel leaks more", BEAT_MS)
        .note(
            "In a short device the drain lowers the barrier: the threshold falls and leakage rises. Faint dots cross under the surface while the gate is dark.",
            "faint dots crossing under the surface, and the gate dark",
        )
        .detail(
            "The drain lowers the source barrier, so the threshold falls with drain voltage.",
            &["DIBL: drain-induced barrier lowering (CHIP_NMOS.txt, section 5)"],
        ),
    Beat::new("body bias: the well shifts the threshold", BEAT_MS)
        .note(
            "Biasing the well raises or lowers the threshold, trading speed against leakage. The violet well is lit beneath the device.",
            "the violet p-well lit beneath the device",
        )
        .detail(
            "The threshold moves with the square root of the well bias.",
            &["BODY BIAS: a square-root law (CHIP_NMOS.txt, section 5)"],
        ),
    Beat::new("the gate wraps the channel: FinFET and GAA", BEAT_MS)
        .note(
            "FinFET and nanosheet gates surround the channel, so the gate, not the drain, owns the barrier. A cyan fin rises through the lit gate.",
            "a cyan fin rising through the amber gate on the silicon",
        )
        .detail(
            "Gate control is what the wrap buys.",
            &["FinFET and nanosheet gates surround the channel (CHIP_NMOS.txt, section 5)"],
        ),
];

const SEC6: &[Beat] = ZE_BEATS;

const SEC7: &[Beat] = &[
    Beat::new("one NMOS: one switch", BEAT_MS)
        .note(
            "Each switch is one NMOS or PMOS. This one is picked out in cyan, with the rest of the chip dimmed.",
            "the NMOS picked out in cyan, the rest of the chip dim",
        )
        .detail(
            "Every transistor on the chip is an NMOS or a PMOS.",
            &["TRANSISTOR COUNT: every one is an NMOS or a PMOS (CHIP_NMOS.txt, section 7)"],
        ),
    Beat::new("billions of switches like this one", BEAT_MS)
        .note(
            "The whole chip, with the NMOS in the middle of the billions of switches like it.",
            "the whole chip in cut-away, the NMOS tagged among the many switches",
        )
        .detail(
            "The count grows with die area and density.",
            &["NVIDIA B200: 208 billion (CHIP_NMOS.txt, section 7 [1])", "AMD MI300X: 153 billion (CHIP_NMOS.txt, section 7 [3])"],
        ),
    Beat::new("contacts and copper wiring", BEAT_MS)
        .note(
            "The switches are wired by tungsten contacts and copper metal. The copper wiring is lit so the metal tiers are visible.",
            "the copper wiring tiers lit, with the contacts and vias below them",
        )
        .detail(
            "Contacts and metal turn billions of switches into one chip.",
            &["NVIDIA H100/H200: 80 billion (CHIP_NMOS.txt, section 7 [2])", "Apple M4: 28 billion (CHIP_NMOS.txt, section 7 [11])"],
        ),
];

const SEC8: &[Beat] = &[
    Beat::new("TSMC: FinFET, N3/N5", BEAT_MS)
        .note(
            "TSMC makes the transistors for most leading chips. This is a FinFET: a cyan fin rises through the gate.",
            "a cyan fin rising through the gate on the silicon",
        )
        .detail(
            "TSMC's 2025 wafer revenue was about NT$3,809B, 74% from 7 nm and below.",
            &["TSMC 2025: NT$3,809B; 3 nm 24%, 7 nm and below 74% (CHIP_NMOS.txt, section 8 [8])"],
        ),
    Beat::new("Intel 18A: RibbonFET, stacked sheets", BEAT_MS)
        .note(
            "Intel builds gate-all-around NMOS and PMOS on 18A. The channel splits into stacked cyan sheets, all surrounded by the gate.",
            "three cyan sheets stacked through the gate",
        )
        .detail(
            "18A has four NMOS threshold options over a 180 mV range; 18A-P adds about +5% NMOS drive.",
            &["4 NMOS Vt options, 180 mV range; 18A-P about +5% NMOS drive (CHIP_NMOS.txt, section 8 [7])"],
        ),
    Beat::new("Synopsys, Cadence: device equations", BEAT_MS)
        .note(
            "Device and circuit simulators model these equations before anything is built. A thin grid lies over the device as a simulator would see it.",
            "a thin grid over the device, the model laid on the cut face",
        )
        .detail(
            "Synopsys and Cadence sell the simulators that model these equations.",
            &["FY25 revenue: Synopsys $7.054B, Cadence $5.297B (CHIP_NMOS.txt, section 8 [10])"],
        ),
];

const SEC9: &[Beat] = &[
    Beat::new("leakage and Vt variability", BEAT_MS)
        .note(
            "At 2 nm-class nodes leakage and threshold variation grow. Faint dots leak under the dark gate.",
            "faint dots leaking under the device, the gate dark",
        )
        .detail(
            "Every switch leaks a little, and billions of them add up.",
            &["Leakage and threshold variability grow at 2 nm-class nodes (CHIP_NMOS.txt, section 9)"],
        ),
    Beat::new("contact resistance limits drive current", BEAT_MS)
        .note(
            "Strain and contact resistance limit drive current as devices shrink. The contact plugs to the source, drain and gate are lit gold.",
            "the contact plugs to source, drain and gate lit gold",
        )
        .detail(
            "Contacts and silicide on the source and drain limit the drive current.",
            &["Strain and contact resistance limit drive current (CHIP_NMOS.txt, section 9)", "Contact resistivity down to 1.5e-9 Ohm.cm2 reported (CHIP_NMOS.txt, section 6)"],
        ),
    Beat::new("very few leading fabs", BEAT_MS)
        .note(
            "The most advanced transistors come from very few fabs. The NMOS is flagged in red on the whole chip.",
            "the NMOS flagged red on the whole chip",
        )
        .detail(
            "Concentration in a few makers is a supply risk.",
            &["TSMC, Intel, Samsung (CHIP_NMOS.txt, section 9)"],
        ),
];

const SEC10: &[Beat] = &[
    Beat::new("transistor counts: NVIDIA, AMD, Apple", BEAT_MS)
        .note(
            "The whole chip, the NMOS highlighted, pulling back slowly. These counts are company and press figures.",
            "the NMOS highlighted on the whole chip, the camera drawing back slowly",
        )
        .detail(
            "Counts come from launch coverage and company statements.",
            &[
                "[1] anandtech.com/show/21310; tomshardware.com Blackwell B200 launch",
                "[3] tweaktown.com/news/94342; digitimes.com/news/a20230614VL200.html",
                "[11] en.wikipedia.org/wiki/Apple_M4; heise.de/en/news (M4 iPad Pro)",
            ],
        ),
    Beat::new("dopants and Si:P: patents and an ECS paper", BEAT_MS)
        .note(
            "The source and drain are highlighted: the arsenic and phosphorus trade-off and the Si:P strain come from these sources.",
            "the source and drain highlighted",
        )
        .detail(
            "The dopant and Si:P figures are taken from these.",
            &[
                "[4] patents.google.com/patent/US4851360; patents.google.com/patent/US8039375",
                "[5] image-ppubs.uspto.gov 7960236; ecs.confex.com/ecs/242/webprogram/Paper166416.html",
            ],
        ),
    Beat::new("swing and DIBL: UCSB lecture and arXiv", BEAT_MS)
        .note(
            "The gate is highlighted: the swing and DIBL equations come from these sources.",
            "the gate highlighted on the chip",
        )
        .detail(
            "The swing and DIBL equations are from these sources.",
            &["[6] courses.ece.ucsb.edu ECE225 Lecture_05; arxiv.org/pdf/1212.2684"],
        ),
    Beat::new("makers and simulators: TSMC, Intel, Synopsys, Cadence", BEAT_MS)
        .note(
            "The whole chip, pulled back. The makers and simulators come from these filings and articles.",
            "the whole chip, pulled back",
        )
        .detail(
            "Company filings and press coverage for the makers and simulators.",
            &[
                "[7] semiengineering.com/extending-18a-with-significant-power-and-performance-gains",
                "[8] sec.gov/Archives/edgar/data/1046179 (6-K); telecomlead.com TSMC 2025 results",
                "[9] sec.gov/Archives/edgar/data/1045810/000104581026000019/q4fy26pr.htm",
                "[10] cimdata.com Synopsys FY2025; seekingalpha.com/pr/20402555 Cadence FY2025",
            ],
        ),
];

// ---- the cells and builders -------------------------------------------------------------------

static OVERVIEW: Cell = std::sync::OnceLock::new();
static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();
static SEC: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_nmos_zoom_a.glb"),
        ZA_BEATS,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_nmos_zoom_b.glb"),
        ZB_BEATS,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_nmos_zoom_c.glb"),
        ZC_BEATS,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_nmos_zoom_d.glb"),
        ZD_BEATS,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_nmos_zoom_e.glb"),
        ZE_BEATS,
    )
}

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the gate stack: metal on high-k",
        build: || -> Box<dyn Scene> { zoom_a() },
    },
    Zoom {
        key: 'b',
        label: "subthreshold, threshold, on",
        build: || -> Box<dyn Scene> { zoom_b() },
    },
    Zoom {
        key: 'c',
        label: "saturation: pinch-off at the drain",
        build: || -> Box<dyn Scene> { zoom_c() },
    },
    Zoom {
        key: 'd',
        label: "short channels: DIBL",
        build: || -> Box<dyn Scene> { zoom_d() },
    },
    Zoom {
        key: 'e',
        label: "dopants and strain",
        build: || -> Box<dyn Scene> { zoom_e() },
    },
];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &SEC[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/chip_nmos_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` section of CHIP_NMOS.txt, in order.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
    section!(1, SEC1),
    section!(2, SEC2),
    section!(3, SEC3),
    section!(4, SEC4),
    section!(5, SEC5),
    section!(6, SEC6),
    section!(7, SEC7),
    section!(8, SEC8),
    section!(9, SEC9),
    section!(10, SEC10),
];

fn overview() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/chip_nmos.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

pub const NODE: Node = Node {
    page: "NMOS",
    overview: Some(overview),
    sections: &SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_explained_and_keyed() {
        let s = overview();
        assert_eq!(s.beats().len(), 6);
        super::super::super::blender::explained(s.as_ref(), "NMOS overview");
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        super::super::super::blender::draws_every_beat(s.as_ref(), "NMOS overview");
    }

    #[test]
    fn zooms_have_their_beats_explained_and_draw() {
        for (name, build, n) in [
            ("zoom a", zoom_a as fn() -> Box<dyn Scene>, 4),
            ("zoom b", zoom_b, 3),
            ("zoom c", zoom_c, 3),
            ("zoom d", zoom_d, 3),
            ("zoom e", zoom_e, 3),
        ] {
            let s = build();
            assert_eq!(s.beats().len(), n, "{name}");
            super::super::super::blender::explained(s.as_ref(), name);
            super::super::super::blender::draws_every_beat(s.as_ref(), name);
        }
    }

    #[test]
    fn sections_match_the_blender_beats_and_draw() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [3, 5, 5, 3, 3, 3, 3, 3, 3, 4]);
        for (i, f) in SECTIONS.iter().enumerate() {
            let s = f();
            super::super::super::blender::explained(s.as_ref(), &format!("section {}", i + 1));
            super::super::super::blender::draws_every_beat(
                s.as_ref(),
                &format!("section {}", i + 1),
            );
        }
    }
}
