// NMOS page (Chip tab): one NMOS transistor in 3D, on the Memory tab's template. The
// overview walks one switching cycle: off, depletion, inversion, linear, saturation,
// turn-off with its leakage, and the chip of billions it is part of. Zooms: a the gate
// stack, b subthreshold and threshold, c pinch-off, d short-channel DIBL, e dopants and
// strain. Sources: section 10 of CHIP_NMOS.txt.

use super::diagrams_scene_chip::{chip_node, ChipNode, ChipState, SecData, ZoomData, BASE, BEAT_MS, DEV, FIN, OVERVIEW_MS, P, STACK};
use crate::ui::anim::Beat;
use poly3d::ChipKey;

const OFF: ChipState = ChipState { vd: 0.3, ..BASE };
const DEPL: ChipState = ChipState { vg: 0.35, vd: 0.3, depletion: 1.0, ..BASE };
const INV: ChipState = ChipState { vg: 0.8, vd: 0.3, depletion: 1.0, inversion: 1.0, ..BASE };
const LIN: ChipState = ChipState { vg: 0.9, vd: 0.4, depletion: 1.0, inversion: 1.0, flow: 0.6, ..BASE };
const SAT: ChipState = ChipState { vg: 0.9, vd: 1.0, depletion: 1.0, inversion: 1.0, pinch: 0.6, flow: 1.0, ..BASE };
const LEAKY: ChipState = ChipState { vd: 0.6, leak: 1.0, ..BASE };
const CHIP: ChipState = ChipState { vg: 0.8, inversion: 1.0, flow: 0.8, contacts: 1.0, silicide: 1.0, metal: 4.0, signal: 1.0, cells: 3.0, ..BASE };

const L_PARTS: &[(P, &str)] = &[(P::Source, "n+ source"), (P::Drain, "n+ drain"), (P::Gate, "gate"), (P::Well, "p-well")];
const L_DEPL: &[(P, &str)] = &[(P::Depletion, "holes pushed away"), (P::Gate, "gate rising")];
const L_INV: &[(P, &str)] = &[(P::Inversion, "electron channel"), (P::Gate, "gate above Vt")];
const L_FLOW: &[(P, &str)] = &[(P::Drift, "electrons: source to drain"), (P::Drain, "drain voltage")];
const L_SAT: &[(P, &str)] = &[(P::Drain, "pinch-off at the drain"), (P::Drift, "current levels out")];
const L_LEAK: &[(P, &str)] = &[(P::Substrate, "leakage under the channel"), (P::Oxide, "through the oxide")];
const L_CHIP: &[(P, &str)] = &[(P::Contact, "contacts"), (P::ThinMetal, "wires"), (P::Gate, "one switch of billions")];

const BEATS: &[Beat] = &[
    Beat::new("off: gate at zero, no path between source and drain", OVERVIEW_MS)
        .note(
            "Two n+ islands, the source and the drain, sit in p-type silicon. With the gate at 0 V the junctions block current: the switch is off.",
            "A planar NMOS: blue source and drain either side of the grey gate, on purple p-type silicon.",
        )
        .detail("An NMOS is a voltage-controlled switch: only the gate's field reaches the silicon.", &["n+ source/drain ~1e20-1e21 /cm3", "p-well ~1e15-1e18 /cm3"]),
    Beat::new("depletion: the gate pushes holes away", OVERVIEW_MS)
        .note(
            "A small positive gate voltage repels the holes under the gate, leaving a region with no free carriers.",
            "Field lines run down from the gate; a purple region opens under it.",
        )
        .detail("Depletion comes before any channel forms.", &["Gate draws no current"]),
    Beat::new("inversion: above the threshold, electrons form a channel", OVERVIEW_MS)
        .note(
            "Past the threshold voltage the gate pulls electrons up to the surface: a thin n-type layer joins source to drain.",
            "A bright cyan sheet appears at the surface under the gate.",
        )
        .detail("The threshold voltage sets when the switch turns on.", &["Inversion at VG > Vt"]),
    Beat::new("linear: a small drain voltage drives electrons across", OVERVIEW_MS)
        .note(
            "With a small drain voltage the channel acts like a resistor: current rises with drain voltage.",
            "Cyan dots run from source to drain through the channel.",
        )
        .detail("Used as a pass switch and in analog circuits.", &["Linear region: small VD"]),
    Beat::new("saturation: the channel pinches off at the drain", OVERVIEW_MS)
        .note(
            "At a high drain voltage the channel thins to nothing at the drain end; current stops rising and levels out.",
            "The bright sheet shortens at the drain end while the dots flow faster.",
        )
        .detail("Digital gates switch in this region.", &["Saturation: VD > VG - Vt"]),
    Beat::new("turn-off: the channel empties, but some leakage remains", OVERVIEW_MS)
        .note(
            "Dropping the gate empties the channel. A little current still sneaks under it and through the thin oxide.",
            "The sheet fades; a few faint dots crawl under the channel and up through the oxide.",
        )
        .detail("Leakage rises about 10x for each 60-100 mV the threshold is lowered.", &["S >= 60 mV/decade at 300 K", "Real S ~70-90 mV/dec"]),
    Beat::new("one switch of billions, wired by contacts and metal", OVERVIEW_MS)
        .note(
            "Contacts land on the source, drain and gate, and metal wires connect switch to switch: a GPU holds tens of billions.",
            "More transistors appear with tungsten contacts and copper wiring above; a signal climbs them.",
        )
        .detail("Every one of them is an NMOS or a PMOS.", &["NVIDIA B200: 208 billion transistors", "AMD MI300X: 153 billion"]),
];

const KEYS: &[ChipKey] = &[
    ChipKey::at(DEV, 1000.0, 0.55, 0.35, OFF).labels(L_PARTS).notes(P::Source, Some(P::Gate)),
    ChipKey::at(FIN, 760.0, 0.30, 0.20, DEPL).labels(L_DEPL).notes(P::Depletion, Some(P::Gate)),
    ChipKey::at(FIN, 760.0, 0.20, 0.25, INV).labels(L_INV).notes(P::Inversion, Some(P::Gate)),
    ChipKey::at(DEV, 900.0, 0.40, 0.30, LIN).labels(L_FLOW).notes(P::Drift, Some(P::Drain)),
    ChipKey::at(DEV, 900.0, 0.60, 0.30, SAT).labels(L_SAT).notes(P::Drain, Some(P::Drift)),
    ChipKey::at(DEV, 950.0, 0.35, 0.20, LEAKY).labels(L_LEAK).notes(P::Substrate, Some(P::Oxide)),
    ChipKey::at(STACK, 2300.0, 0.45, 0.30, CHIP).labels(L_CHIP).notes(P::Contact, Some(P::ThinMetal)),
];

// ---- a-e -----------------------------------------------------------------------

const ZA_B: &[Beat] = &[
    Beat::new("the gate stack, cut open", BEAT_MS)
        .note("Cut through the gate: a metal gate on a thin high-k dielectric over the silicon.", "The front of the gate is cut away; the yellow dielectric shows under it.")
        .detail("About 1 nm EOT class.", &["Metal gate + high-k (HfO2) + thin SiO2"]),
    Beat::new("the gate's field reaches through the oxide", BEAT_MS)
        .note("A gate voltage sets up a field across the dielectric that controls the silicon below.", "Field lines run down; the channel forms under the gate.")
        .detail("No current flows into the gate, only its field.", &["Capacitive control"]),
    Beat::new("a thinner, higher-k layer: more control, less leakage", BEAT_MS)
        .note("High-k material lets the layer stay physically thick enough to stop tunnelling while acting electrically thin.", "The dielectric thickens and brightens; leakage through it fades.")
        .detail("See the GATE STACK node.", &["High-k replaced SiO2 gates"]),
];
const ZA_K: &[ChipKey] = &[
    ChipKey::at(FIN, 700.0, 0.25, 0.25, ChipState { cut: 1.0, hik: 0.3, ..BASE }).labels(&[(P::Gate, "metal gate"), (P::Oxide, "dielectric")]).title("the gate stack", "cut open at the front"),
    ChipKey::at(FIN, 680.0, 0.15, 0.20, ChipState { cut: 1.0, hik: 0.3, vg: 1.0, inversion: 1.0, depletion: 1.0, ..BASE }).labels(&[(P::Oxide, "field across the dielectric"), (P::Inversion, "channel")]).title("gate voltage on", "the field controls the silicon"),
    ChipKey::at(FIN, 680.0, 0.30, 0.22, ChipState { cut: 1.0, hik: 1.0, vg: 1.0, inversion: 1.0, ..BASE }).labels(&[(P::Oxide, "high-k: thick but electrically thin")]).title("high-k dielectric", "~1 nm EOT class"),
];

const ZB_B: &[Beat] = &[
    Beat::new("below threshold: leakage only", BEAT_MS)
        .note("Below the threshold a weak current still flows, rising exponentially with gate voltage.", "A few faint dots cross under the channel.")
        .detail("This is the off-state leakage.", &["Id ~ exp(VG) below Vt"]),
    Beat::new("at threshold: the channel forms", BEAT_MS)
        .note("At the threshold voltage strong inversion starts and the current climbs steeply.", "The cyan sheet appears and dots start to flow.")
        .detail("S = (kT/q) ln10 (1 + Cdep/Cox).", &[">= 60 mV/decade at 300 K"]),
    Beat::new("above threshold: fully on", BEAT_MS)
        .note("Well above threshold the current grows more slowly as the electrons reach their velocity limit.", "A dense stream of dots runs source to drain.")
        .detail("Lower Vt means more on-current and more leakage.", &["~10x leakage per 60-100 mV of Vt"]),
];
const ZB_K: &[ChipKey] = &[
    ChipKey::at(DEV, 900.0, 0.40, 0.25, ChipState { vg: 0.2, vd: 0.6, leak: 1.0, ..BASE }).labels(&[(P::Substrate, "subthreshold leakage")]).title("subthreshold", "Id rises ~10x per 60-90 mV"),
    ChipKey::at(DEV, 880.0, 0.45, 0.28, ChipState { vg: 0.55, vd: 0.6, inversion: 0.7, depletion: 1.0, flow: 0.4, ..BASE }).labels(&[(P::Inversion, "threshold: inversion starts")]).title("threshold", "VG = Vt"),
    ChipKey::at(DEV, 880.0, 0.55, 0.30, ChipState { vg: 1.0, vd: 0.6, inversion: 1.0, depletion: 1.0, flow: 1.0, ..BASE }).labels(&[(P::Drift, "on: full current")]).title("on", "velocity-saturated"),
];

const ZC_B: &[Beat] = &[
    Beat::new("low drain voltage: an even channel", BEAT_MS)
        .note("With a small drain voltage the channel is the same thickness end to end.", "An even cyan sheet, dots moving gently.")
        .detail("Current rises with drain voltage.", &["Linear region"]),
    Beat::new("raise the drain: the channel thins at the drain end", BEAT_MS)
        .note("The drain voltage reduces the gate's pull near the drain, so the channel thins there.", "The sheet tapers towards the drain.")
        .detail("This is where pinch-off begins.", &["VD -> VG - Vt"]),
    Beat::new("pinch-off: current levels out", BEAT_MS)
        .note("Past pinch-off the electrons cross the last gap in the high field, and current barely rises with more drain voltage.", "The sheet stops short of the drain; the dots race across the gap.")
        .detail("Digital switching happens in saturation.", &["Saturation: current flat in VD"]),
];
const ZC_K: &[ChipKey] = &[
    ChipKey::at(DEV, 800.0, 0.25, 0.30, ChipState { vg: 0.9, vd: 0.2, inversion: 1.0, flow: 0.4, ..BASE }).labels(&[(P::Inversion, "even channel")]).title("linear", "small drain voltage"),
    ChipKey::at(DEV, 780.0, 0.35, 0.30, ChipState { vg: 0.9, vd: 0.6, inversion: 1.0, pinch: 0.3, flow: 0.7, ..BASE }).labels(&[(P::Drain, "drain raised")]).title("thinning", "the drain end weakens"),
    ChipKey::at(DEV, 780.0, 0.45, 0.30, ChipState { vg: 0.9, vd: 1.0, inversion: 1.0, pinch: 0.8, flow: 1.0, ..BASE }).labels(&[(P::Drain, "pinched off")]).title("saturation", "current levels out"),
];

const ZD_B: &[Beat] = &[
    Beat::new("a long channel: the gate owns the barrier", BEAT_MS)
        .note("In a long device the gate alone sets the barrier between source and drain.", "A long gate; almost no leakage.")
        .detail("The threshold is steady.", &["Long channel"]),
    Beat::new("shrink the gate: the drain starts to help", BEAT_MS)
        .note("In a short channel the drain's field reaches the source side and lowers the barrier: drain-induced barrier lowering (DIBL).", "The gate shortens and leakage starts to crawl under it.")
        .detail("The threshold falls as the channel shrinks.", &["Vt roll-off"]),
    Beat::new("raise the drain: more leakage", BEAT_MS)
        .note("A higher drain voltage lowers the barrier more, so leakage rises with drain voltage.", "Drain voltage up; leakage grows.")
        .detail("Wrapping the gate around the channel fights this.", &["FinFET and GAA"]),
];
const ZD_K: &[ChipKey] = &[
    ChipKey::at(DEV, 900.0, 0.45, 0.30, ChipState { gate_len: 1.4, vd: 0.4, ..BASE }).labels(&[(P::Gate, "long gate")]).title("long channel", "the gate owns the barrier"),
    ChipKey::at(DEV, 850.0, 0.40, 0.28, ChipState { gate_len: 0.55, vd: 0.4, leak: 0.5, ..BASE }).labels(&[(P::Gate, "short gate"), (P::Substrate, "leakage starts")]).title("short channel", "DIBL"),
    ChipKey::at(DEV, 850.0, 0.50, 0.28, ChipState { gate_len: 0.55, vd: 1.0, leak: 1.0, ..BASE }).labels(&[(P::Drain, "high drain voltage"), (P::Substrate, "more leakage")]).title("DIBL", "Vt falls with drain voltage"),
];

const ZE_B: &[Beat] = &[
    Beat::new("dopants in the source and drain", BEAT_MS)
        .note("Arsenic or phosphorus atoms make the source and drain n-type. Arsenic diffuses slowly and gives sharp junctions.", "Dopant atoms glow in the source and drain.")
        .detail("Phosphorus activates better but spreads deeper.", &["As: shallow, abrupt", "P: deeper, better activation"]),
    Beat::new("Si:P epitaxy and halo pockets", BEAT_MS)
        .note("Phosphorus-doped silicon grown in place reaches about 1.2e21 /cm3; halo pockets of the opposite type beside the channel stop punch-through.", "Halo pockets appear at the channel ends.")
        .detail("Contact resistivity to 1.5e-9 Ohm.cm2 reported.", &["Si:P ~1.2e21 /cm3, 0.3 mOhm.cm"]),
    Beat::new("tensile strain speeds electrons", BEAT_MS)
        .note("Si:P stretches the channel; tensile strain raises electron mobility, so the switch drives more current.", "Arrows pull along the channel; dots flow faster.")
        .detail("PMOS uses compressive strain instead.", &["Tensile strain for NMOS"]),
];
const ZE_K: &[ChipKey] = &[
    ChipKey::at(DEV, 850.0, 0.45, 0.35, ChipState { dopants: 1.0, ..BASE }).labels(&[(P::Dopants, "As / P atoms")]).title("dopants", "n+ source and drain"),
    ChipKey::at(DEV, 820.0, 0.30, 0.25, ChipState { dopants: 0.6, halo: 1.0, cut: 0.5, ..BASE }).labels(&[(P::Halo, "halo pocket"), (P::Source, "Si:P epi")]).title("Si:P and halos", "1.2e21 /cm3"),
    ChipKey::at(DEV, 850.0, 0.50, 0.30, ChipState { strain: 1.0, vg: 0.9, inversion: 1.0, flow: 1.0, ..BASE }).labels(&[(P::Channel, "stretched channel")]).title("tensile strain", "faster electrons"),
];

const Z: [ZoomData; 5] = [
    ('a', "the gate stack: metal on high-k", ZA_B, ZA_K),
    ('b', "subthreshold, threshold, on", ZB_B, ZB_K),
    ('c', "saturation: pinch-off at the drain", ZC_B, ZC_K),
    ('d', "short channels: DIBL", ZD_B, ZD_K),
    ('e', "dopants and strain", ZE_B, ZE_K),
];

// ---- 1-9 -----------------------------------------------------------------------

const S1_B: &[Beat] = &[
    Beat::new("off: no channel", BEAT_MS).note("Gate at zero: the source and drain are isolated.", "The device with the gate dark.").detail("A voltage-controlled switch.", &["OFF STATE"]),
    Beat::new("on: an electron channel", BEAT_MS).note("Gate high: electrons form a channel at the surface.", "The cyan sheet appears.").detail("Only the field reaches the silicon.", &["INVERSION"]),
    Beat::new("current flows", BEAT_MS).note("The drain voltage pulls electrons across from the source.", "Dots run source to drain.").detail("Then the gate drops and it stops.", &["SATURATION"]),
];
const S1_K: &[ChipKey] = &[
    ChipKey::at(DEV, 1000.0, 0.50, 0.35, OFF).labels(L_PARTS).title("off", "gate at 0 V"),
    ChipKey::at(FIN, 760.0, 0.25, 0.25, INV).labels(L_INV).title("on", "gate above threshold"),
    ChipKey::at(DEV, 900.0, 0.50, 0.30, SAT).labels(L_FLOW).title("conducting", "electrons source to drain"),
];

const S2_B: &[Beat] = &[
    Beat::new("N+ SOURCE", BEAT_MS).note("Heavily doped n-type silicon, usually grounded.", "The source lights; the rest greys.").detail("~1e20-1e21 /cm3.", &["As / P"]),
    Beat::new("GATE STACK", BEAT_MS).note("Metal gate on high-k dielectric: the switch input.", "The gate lights.").detail("~1 nm EOT class.", &["Metal + high-k"]),
    Beat::new("N+ DRAIN", BEAT_MS).note("The output node, tied to the load or VDD.", "The drain lights.").detail("Same doping as the source.", &["Output"]),
    Beat::new("P-WELL", BEAT_MS).note("The p-type body the device sits in; holes are the majority carrier.", "The well lights.").detail("~1e15-1e18 /cm3 boron.", &["Body"]),
    Beat::new("spacers and halos", BEAT_MS).note("Spacers set where the source/drain extensions start; halo pockets stop punch-through.", "The spacers and halos light.").detail("Small parts, big effect on leakage.", &["Spacer, halo"]),
    Beat::new("STI isolation", BEAT_MS).note("Shallow trench isolation: oxide walls between neighbouring transistors.", "The trench oxide at the sides lights.").detail("Keeps neighbours from leaking into each other.", &["STI"]),
];
const S2_K: &[ChipKey] = &[
    ChipKey::at(DEV, 850.0, 0.30, 0.35, BASE.spot(P::Source)).labels(&[(P::Source, "n+ source")]),
    ChipKey::at(FIN, 700.0, 0.30, 0.25, ChipState { cut: 1.0, ..BASE }.spot(P::Gate)).labels(&[(P::Gate, "gate stack")]),
    ChipKey::at(DEV, 850.0, 0.70, 0.35, BASE.spot(P::Drain)).labels(&[(P::Drain, "n+ drain")]),
    ChipKey::at(DEV, 950.0, 0.50, 0.15, BASE.spot(P::Well)).labels(&[(P::Well, "p-well")]),
    ChipKey::at(DEV, 760.0, 0.25, 0.20, ChipState { halo: 1.0, cut: 0.6, ..BASE }.spot(P::Spacer).spot(P::Halo)).labels(&[(P::Spacer, "spacer"), (P::Halo, "halo")]),
    ChipKey::at(DEV, 950.0, 0.80, 0.30, BASE.spot(P::Sti)).labels(&[(P::Sti, "STI oxide")]),
];

const S3_B: &[Beat] = &[
    Beat::new("1. OFF STATE", BEAT_MS).note("Gate at 0 V; the junctions block current.", "The device at rest.").detail("Only leakage.", &["VG = 0"]),
    Beat::new("2. DEPLETION", BEAT_MS).note("A small gate voltage pushes holes away.", "A depletion region opens.").detail("No channel yet.", &["0 < VG < Vt"]),
    Beat::new("3. INVERSION", BEAT_MS).note("Above threshold, electrons gather into a channel.", "The cyan sheet forms.").detail("The switch is on.", &["VG > Vt"]),
    Beat::new("4. LINEAR, then SATURATION", BEAT_MS).note("The drain voltage drives the electrons; at high drain voltage the channel pinches off.", "Dots flow; the sheet tapers at the drain.").detail("Current levels out.", &["VD > VG - Vt"]),
    Beat::new("5. TURN-OFF", BEAT_MS).note("The gate drops and the channel empties.", "Everything fades back to rest.").detail("Ready for the next cycle.", &["VG -> 0"]),
];
const S3_K: &[ChipKey] = &[
    ChipKey::at(DEV, 950.0, 0.50, 0.35, OFF).title("1 off", "VG = 0"),
    ChipKey::at(FIN, 760.0, 0.30, 0.22, DEPL).title("2 depletion", "holes pushed away"),
    ChipKey::at(FIN, 760.0, 0.20, 0.25, INV).title("3 inversion", "channel forms"),
    ChipKey::at(DEV, 900.0, 0.55, 0.30, SAT).title("4 saturation", "pinch-off"),
    ChipKey::at(DEV, 950.0, 0.45, 0.35, ChipState { vd: 0.3, leak: 0.3, ..BASE }).title("5 turn-off", "channel empties"),
];

const S4_B: &[Beat] = ZB_B;
const S4_K: &[ChipKey] = ZB_K;

const S5_B: &[Beat] = &[
    Beat::new("DIBL: a short channel leaks more", BEAT_MS).note("In a short device the drain lowers the barrier: the threshold falls and leakage rises.", "A short gate with leakage under it.").detail("Vt roll-off.", &["DIBL"]),
    Beat::new("BODY BIAS: the well shifts the threshold", BEAT_MS).note("Biasing the well raises or lowers the threshold, trading speed against leakage.", "The well lights; leakage drops.").detail("A square-root law.", &["Body bias"]),
    Beat::new("wrapping the gate fights both", BEAT_MS).note("FinFET and nanosheet gates surround the channel so the gate, not the drain, owns the barrier.", "The channel rises into fins inside the gate.").detail("See FINFET and GAA.", &["Gate control"]),
];
const S5_K: &[ChipKey] = &[
    ChipKey::at(DEV, 850.0, 0.45, 0.28, ChipState { gate_len: 0.55, vd: 1.0, leak: 1.0, ..BASE }).labels(&[(P::Substrate, "leakage")]).title("DIBL", "drain lowers the barrier"),
    ChipKey::at(DEV, 950.0, 0.45, 0.15, ChipState { gate_len: 0.55, vd: 1.0, leak: 0.3, ..BASE }.spot(P::Well)).labels(&[(P::Well, "body bias")]).title("body bias", "well voltage shifts Vt"),
    ChipKey::at(FIN, 760.0, 0.30, 0.25, ChipState { arch: 1.0, gate_len: 0.7, cut: 1.0, ..BASE }).labels(&[(P::Fin, "fin inside the gate")]).title("wrap the gate", "FinFET, GAA"),
];

const S6_B: &[Beat] = ZE_B;
const S6_K: &[ChipKey] = ZE_K;

const S7_B: &[Beat] = &[
    Beat::new("one transistor", BEAT_MS).note("Each switch is one NMOS or PMOS.", "One transistor, on.").detail("TRANSISTOR COUNT starts here.", &["1"]),
    Beat::new("rows of them", BEAT_MS).note("Transistors sit side by side by the billion.", "More transistors appear in a row.").detail("Count grows with die area and density.", &["Apple M4: 28 billion"]),
    Beat::new("wired into a GPU", BEAT_MS).note("Wired together by contacts and metal they make a chip.", "Contacts and metal rise over the row.").detail("B200: 208 billion across two dies.", &["B200 208B", "MI300X 153B", "H100 80B"]),
];
const S7_K: &[ChipKey] = &[
    ChipKey::at(DEV, 1000.0, 0.50, 0.35, LIN).title("one switch", "NMOS"),
    ChipKey::at([0.0, 30.0, 0.0], 2200.0, 0.40, 0.45, ChipState { cells: 5.0, ..LIN }).title("side by side", "billions per chip"),
    ChipKey::at(STACK, 2600.0, 0.45, 0.35, ChipState { cells: 5.0, contacts: 1.0, metal: 6.0, signal: 1.0, ..LIN }).title("wired up", "B200: 208 billion"),
];

const S8_B: &[Beat] = &[
    Beat::new("TSMC (TSM): builds them for NVIDIA, AMD, Apple", BEAT_MS).note("TSMC makes the transistors for most leading chips.", "A FinFET, the TSMC N3/N5 type.").detail("3 nm 24%, 7 nm and below 74% of 2025 wafer revenue.", &["TSMC 2025: NT$3,809B"]),
    Beat::new("Intel (INTC): RibbonFET on 18A", BEAT_MS).note("Intel builds gate-all-around NMOS and PMOS on 18A, with 4 threshold options each.", "The channel splits into stacked sheets.").detail("18A-P: about +5% NMOS drive current.", &["4 NMOS Vt options, 180 mV range"]),
    Beat::new("Synopsys (SNPS), Cadence (CDNS): the simulators", BEAT_MS).note("Device and circuit simulators model these equations before anything is built.", "The device cut open, as a simulator would see it.").detail("FY25 revenue $7.054B and $5.297B.", &["TCAD and SPICE"]),
];
const S8_K: &[ChipKey] = &[
    ChipKey::at(FIN, 900.0, 0.40, 0.30, ChipState { arch: 1.0, vg: 0.8, inversion: 1.0, flow: 0.8, ..BASE }).title("TSMC", "FinFET, N3/N5"),
    ChipKey::at(FIN, 800.0, 0.30, 0.25, ChipState { arch: 2.0, cut: 1.0, vg: 0.8, flow: 0.8, ..BASE }).title("Intel 18A", "RibbonFET (GAA)"),
    ChipKey::at(FIN, 760.0, 0.20, 0.25, ChipState { cut: 1.0, depletion: 1.0, inversion: 1.0, vg: 0.8, ..BASE }).title("Synopsys, Cadence", "device and circuit simulation"),
];

const S9_B: &[Beat] = &[
    Beat::new("leakage and variability", BEAT_MS).note("At 2 nm-class nodes, leakage and threshold variation grow.", "Leakage crawls under a short channel.").detail("Every switch leaks a little; billions add up.", &["Leakage"]),
    Beat::new("contact resistance", BEAT_MS).note("Strain and contact resistance limit drive current as devices shrink.", "Contacts and silicide on the source and drain light up.").detail("See the CONTACTS node.", &["Contact resistance"]),
    Beat::new("few fabs", BEAT_MS).note("The most advanced transistors come from very few fabs.", "A row of transistors.").detail("Concentration is a supply risk.", &["TSMC, Intel, Samsung"]),
];
const S9_K: &[ChipKey] = &[
    ChipKey::at(DEV, 850.0, 0.40, 0.25, ChipState { gate_len: 0.6, vd: 1.0, leak: 1.0, ..BASE }).title("leakage", "and Vt variability"),
    ChipKey::at(DEV, 900.0, 0.55, 0.40, ChipState { contacts: 1.0, silicide: 1.0, ..BASE }.spot(P::Contact).spot(P::Silicide)).title("contact resistance", "limits drive current"),
    ChipKey::at([0.0, 30.0, 0.0], 2200.0, 0.40, 0.45, ChipState { cells: 5.0, ..LIN }).title("concentration", "very few leading fabs"),
];

const S: [SecData; 9] = [(S1_B, S1_K), (S2_B, S2_K), (S3_B, S3_K), (S4_B, S4_K), (S5_B, S5_K), (S6_B, S6_K), (S7_B, S7_K), (S8_B, S8_K), (S9_B, S9_K)];

chip_node!(ZOOMS, SECTIONS, Z, S);

pub static NODE: ChipNode = ChipNode {
    page: "NMOS",
    beats: BEATS,
    keys: KEYS,
    zooms: &ZOOMS,
    zoom_data: &Z,
    sections: &SECTIONS,
    section_data: &S,
};
