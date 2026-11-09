// PMOS page (Chip tab): the hole-carrying transistor and its pairing with an NMOS,
// in 3D on the Memory tab's template. Overview: the PMOS at rest, gate low and holes
// flowing, the SiGe squeeze, then the CMOS inverter flipping both ways. Zooms: a the
// n-well, b SiGe strain, c the inverter, d width ratio, e GAA PFET. Sources: section
// 10 of CHIP_PMOS.txt.

use super::diagrams_scene_chip::{chip_node, ChipNode, ChipState, SecData, ZoomData, BASE, BEAT_MS, DEV, FIN, OVERVIEW_MS, P, STACK};
use crate::ui::anim::Beat;
use poly3d::ChipKey;

const PM: ChipState = ChipState { pmos: 1.0, vg: 1.0, vd: 0.3, ..BASE };
const PON: ChipState = ChipState { pmos: 1.0, vg: 0.0, vd: 0.6, inversion: 1.0, depletion: 1.0, flow: 1.0, ..BASE };
const SIGE: ChipState = ChipState { strain: 1.0, dopants: 1.0, ..PON };
/// inverter, input 0: PMOS (cell 0) on, NMOS (cell 1) off
const INV0: ChipState = ChipState { pmos: 1.0, pair: 1.0, cells: 2.0, vg: 0.0, inversion: 1.0, flow: 1.0, inv2: 0.0, flow2: 0.0, contacts: 1.0, ..BASE };
/// inverter, input 1: PMOS off, NMOS on
const INV1: ChipState = ChipState { vg: 1.0, inversion: 0.0, flow: 0.0, inv2: 1.0, flow2: 1.0, ..INV0 };
const ROW: ChipState = ChipState { cells: 4.0, contacts: 1.0, metal: 2.0, signal: 1.0, ..INV0 };
const PAIR_VIEW: [f64; 3] = [0.0, 60.0, 0.0];

const BEATS: &[Beat] = &[
    Beat::new("a PMOS: p+ source and drain in an n-well", OVERVIEW_MS)
        .note("The mirror of an NMOS: p+ source and drain sit in n-type silicon, and the gate is held high to keep it off.", "Pink source and drain in a blue-grey n-well.")
        .detail("The n-well is tied to Vdd through an n+ tap.", &["p+ S/D: boron-doped SiGe", "n-well tied to Vdd"]),
    Beat::new("gate low: holes form a channel", OVERVIEW_MS)
        .note("Pulling the gate low draws holes to the surface: a p-type channel joins source to drain and current flows.", "An orange channel appears and orange holes flow source to drain.")
        .detail("Holes are slower than electrons.", &["Si hole mobility ~450 vs electrons ~1400 cm2/Vs"]),
    Beat::new("SiGe squeezes the channel to speed the holes", OVERVIEW_MS)
        .note("The source and drain are regrown as SiGe, which is bigger than silicon and squeezes the channel along the current: holes move faster.", "Arrows press inward on the channel; boron atoms glow in the source and drain.")
        .detail("Compressive strain for PMOS, tensile for NMOS.", &["Intel 90 nm: PMOS +25% drive"]),
    Beat::new("CMOS: a PMOS on top of an NMOS makes an inverter", OVERVIEW_MS)
        .note("Gates tied, drains tied: the PMOS pulls the output up to Vdd, the NMOS pulls it down to ground.", "A PMOS and an NMOS side by side with contacts.")
        .detail("This pair is the basic CMOS gate.", &["INVERTER: out = NOT in"]),
    Beat::new("input 0: PMOS on, NMOS off, output high", OVERVIEW_MS)
        .note("A low input turns the PMOS on and the NMOS off: the output charges to Vdd.", "Holes flow in the PMOS; the NMOS is dark.")
        .detail("No path from Vdd to ground.", &["In = 0 -> Out = 1"]),
    Beat::new("input 1: PMOS off, NMOS on, output low", OVERVIEW_MS)
        .note("A high input turns the PMOS off and the NMOS on: the output discharges to ground.", "The PMOS goes dark; electrons flow in the NMOS.")
        .detail("Only the flip itself draws current.", &["CMOS power ~ C x V^2 x f"]),
    Beat::new("rows of pairs: standard cells", OVERVIEW_MS)
        .note("Logic is tiled from standard cells: PMOS strip on top, NMOS below, rails along the edges, wired by metal.", "Pairs repeat in a row with metal above.")
        .detail("Cell height is counted in metal tracks.", &["ASAP7: 9-track and 7.5-track cells"]),
];
const KEYS: &[ChipKey] = &[
    ChipKey::at(DEV, 1000.0, 0.55, 0.35, PM).labels(&[(P::Source, "p+ source"), (P::Drain, "p+ drain"), (P::Well, "n-well")]).notes(P::Source, Some(P::Well)),
    ChipKey::at(DEV, 900.0, 0.40, 0.30, PON).labels(&[(P::Drift, "holes: source to drain"), (P::Gate, "gate low")]).notes(P::Drift, Some(P::Gate)),
    ChipKey::at(DEV, 850.0, 0.50, 0.30, SIGE).labels(&[(P::Channel, "squeezed channel"), (P::Dopants, "SiGe:B")]).notes(P::Channel, Some(P::Source)),
    ChipKey::at(PAIR_VIEW, 1500.0, 0.40, 0.40, ChipState { vg: 0.5, inversion: 0.0, flow: 0.0, ..INV0 }).labels(&[(P::Source, "PMOS"), (P::Contact, "tied gates and drains")]).notes(P::Contact, Some(P::Gate)),
    ChipKey::at(PAIR_VIEW, 1450.0, 0.35, 0.35, INV0).labels(&[(P::Drift, "PMOS on: output to Vdd")]).notes(P::Drift, Some(P::Contact)),
    ChipKey::at(PAIR_VIEW, 1450.0, 0.55, 0.35, INV1).labels(&[(P::Drain, "NMOS on: output to ground")]).notes(P::Drain, Some(P::Contact)),
    ChipKey::at(STACK, 2600.0, 0.45, 0.35, ROW).labels(&[(P::ThinMetal, "rails and wiring"), (P::Gate, "standard cells")]).notes(P::Gate, Some(P::ThinMetal)),
];

const ZA_B: &[Beat] = &[
    Beat::new("the n-well: n-type silicon under the PMOS", BEAT_MS).note("The PMOS sits in an n-type well inside the p-type substrate.", "The n-well lights.").detail("Its junctions with the p+ regions are reverse-biased.", &["N-WELL"]),
    Beat::new("tied to Vdd through a tap", BEAT_MS).note("A tap ties the well to Vdd so the junctions stay reverse-biased.", "Contacts rise from the well side.").detail("Tap cells do this along each row.", &["TAP CELL"]),
    Beat::new("the n-well keeps the PMOS isolated", BEAT_MS).note("With the well biased, current only flows through the channel when the gate is low.", "The channel conducts; the well stays dark.").detail("Latch-up prevention depends on these taps.", &["Latch-up"]),
];
const ZA_K: &[ChipKey] = &[
    ChipKey::at(DEV, 950.0, 0.45, 0.15, PM.spot(P::Well)).labels(&[(P::Well, "n-well")]).title("n-well", "n-type tub"),
    ChipKey::at(DEV, 950.0, 0.60, 0.30, ChipState { contacts: 1.0, ..PM }.spot(P::Contact).spot(P::Well)).labels(&[(P::Contact, "tap to Vdd")]).title("well tap", "tied to Vdd"),
    ChipKey::at(DEV, 900.0, 0.45, 0.25, PON).labels(&[(P::Drift, "only the channel conducts")]).title("isolated", "reverse-biased junctions"),
];

const ZB_B: &[Beat] = &[
    Beat::new("boron-doped SiGe source and drain", BEAT_MS).note("The source and drain are etched out and regrown as boron-doped SiGe.", "Boron atoms glow in the pink source and drain.").detail("Boron diffuses fast: a risk to the channel.", &["BORON DOPING"]),
    Beat::new("SiGe squeezes the channel", BEAT_MS).note("Germanium atoms are larger, so the regrown SiGe pushes on the channel along the current direction.", "Arrows press inward.").detail("Compressive strain helps holes.", &["SiGe STRESSOR"]),
    Beat::new("faster holes, more drive", BEAT_MS).note("Strain raises hole mobility; Intel's 90 nm strain gave PMOS 25% more drive for about 2% cost.", "Holes stream faster through the squeezed channel.").detail("Intel 2004: 0.72 mA/um at 1.2 V.", &["+25% PMOS drive", "~2% process cost"]),
];
const ZB_K: &[ChipKey] = &[
    ChipKey::at(DEV, 850.0, 0.45, 0.35, ChipState { dopants: 1.0, ..PM }).labels(&[(P::Dopants, "SiGe:B")]).title("SiGe:B", "regrown source and drain"),
    ChipKey::at(DEV, 820.0, 0.30, 0.25, ChipState { strain: 1.0, dopants: 0.5, ..PM }).labels(&[(P::Channel, "compressed")]).title("compressive strain", "along the channel"),
    ChipKey::at(DEV, 850.0, 0.50, 0.30, SIGE).labels(&[(P::Drift, "faster holes")]).title("more drive", "Intel 90 nm: +25%"),
];

const ZC_B: &[Beat] = &[
    Beat::new("PMOS pull-up, NMOS pull-down", BEAT_MS).note("An inverter: PMOS to Vdd, NMOS to ground, gates and drains tied.", "The pair side by side, both idle.").detail("The basic CMOS gate.", &["INVERTER"]),
    Beat::new("input low: output high", BEAT_MS).note("The PMOS conducts and charges the output; the NMOS is off.", "Holes flow in the PMOS.").detail("No Vdd-to-ground path.", &["In 0 -> Out 1"]),
    Beat::new("input high: output low", BEAT_MS).note("The NMOS conducts and discharges the output; the PMOS is off.", "Electrons flow in the NMOS.").detail("Power only on the flip: C x V^2 x f.", &["CMOS POWER"]),
];
const ZC_K: &[ChipKey] = &[
    ChipKey::at(PAIR_VIEW, 1400.0, 0.40, 0.40, ChipState { vg: 0.5, inversion: 0.0, flow: 0.0, ..INV0 }).labels(&[(P::Source, "PMOS"), (P::Drain, "NMOS")]).title("CMOS inverter", "gates tied, drains tied"),
    ChipKey::at(PAIR_VIEW, 1400.0, 0.35, 0.35, INV0).labels(&[(P::Drift, "PMOS conducts")]).title("in = 0", "out = 1"),
    ChipKey::at(PAIR_VIEW, 1400.0, 0.55, 0.35, INV1).labels(&[(P::Drain, "NMOS conducts")]).title("in = 1", "out = 0"),
];

const ZD_B: &[Beat] = &[
    Beat::new("holes are about 3x slower", BEAT_MS).note("In silicon holes move at about a third of electrons' mobility.", "Two transistors: holes in one crawl, electrons in the other race.").detail("mu_n ~1400, mu_p ~450 cm2/Vs.", &["HOLE MOBILITY"]),
    Beat::new("make the PMOS wider", BEAT_MS).note("Equal drive needs mu_n x Wn = mu_p x Wp, so the PMOS is about 2-2.5x wider.", "The PMOS side widens into more fins.").detail("Equal rise and fall times.", &["WIDTH RATIO ~2-2.5"]),
    Beat::new("in fins, width comes in whole fins", BEAT_MS).note("In FinFET and GAA, width is counted in fins or sheets, so the PMOS gets more of them; strain shrinks the ratio.", "Fins standing in both transistors.").detail("Quantised width.", &["FinFET / GAA"]),
];
const ZD_K: &[ChipKey] = &[
    ChipKey::at(PAIR_VIEW, 1400.0, 0.40, 0.35, ChipState { vg: 0.0, inversion: 1.0, flow: 0.4, inv2: 1.0, flow2: 1.0, ..INV0 }).labels(&[(P::Drift, "slow holes")]).title("hole mobility", "~450 vs ~1400"),
    ChipKey::at(PAIR_VIEW, 1350.0, 0.30, 0.40, ChipState { arch: 1.0, vg: 0.0, inversion: 1.0, flow: 1.0, inv2: 1.0, flow2: 1.0, ..INV0 }).labels(&[(P::Fin, "more PMOS width")]).title("width ratio", "Wp/Wn ~2-2.5"),
    ChipKey::at(PAIR_VIEW, 1300.0, 0.25, 0.30, ChipState { arch: 1.0, cut: 1.0, vg: 0.0, inversion: 1.0, flow: 1.0, inv2: 1.0, flow2: 1.0, ..INV0 }).labels(&[(P::Fin, "width in whole fins")]).title("quantised width", "fins or sheets"),
];

const ZE_B: &[Beat] = &[
    Beat::new("PMOS as stacked sheets", BEAT_MS).note("In gate-all-around, the PMOS channel is a stack of thin sheets the gate surrounds.", "The channel splits into sheets.").detail("See the GAA node.", &["GAA PFET"]),
    Beat::new("SiGe sheets, about 1 GPa of strain", BEAT_MS).note("IBM's SiGe nanosheet pFET squeezed the sheets to about 1 GPa.", "Arrows press on the sheets; holes flow.").detail("+100% peak hole mobility, -40% channel R.", &["IBM SiGe NS pFET"]),
    Beat::new("germanium: even faster holes", BEAT_MS).note("Germanium's hole mobility is about 1900 against silicon's 450, but its oxide and leakage are hard.", "Holes race through the sheets.").detail("Boron diffusion is another obstacle.", &["GE CHANNEL ~1900 cm2/Vs"]),
];
const ZE_K: &[ChipKey] = &[
    ChipKey::at(FIN, 800.0, 0.30, 0.25, ChipState { arch: 2.0, cut: 1.0, ..PM }).labels(&[(P::Sheet, "PMOS sheets")]).title("GAA PFET", "stacked sheets"),
    ChipKey::at(FIN, 780.0, 0.20, 0.22, ChipState { arch: 2.0, cut: 1.0, strain: 1.0, ..PON }).labels(&[(P::Sheet, "SiGe, ~1 GPa")]).title("strained SiGe sheets", "IBM: +100% mobility"),
    ChipKey::at(FIN, 780.0, 0.35, 0.25, ChipState { arch: 2.0, cut: 1.0, strain: 1.0, ..PON }).labels(&[(P::Drift, "Ge: ~1900 cm2/Vs")]).title("germanium channel", "fast holes, hard oxide"),
];

const Z: [ZoomData; 5] = [
    ('a', "the n-well and its tap", ZA_B, ZA_K),
    ('b', "SiGe strain: squeezing the channel", ZB_B, ZB_K),
    ('c', "the CMOS inverter", ZC_B, ZC_K),
    ('d', "width ratio: making up for slow holes", ZD_B, ZD_K),
    ('e', "GAA PFET and germanium", ZE_B, ZE_K),
];

const S1_B: &[Beat] = &[
    Beat::new("a PMOS at rest", BEAT_MS).note("p+ source and drain in an n-well, gate high: off.", "The PMOS, dark.").detail("Mirror of the NMOS.", &["PMOS"]),
    Beat::new("gate low: holes flow", BEAT_MS).note("A low gate opens a hole channel.", "Holes flow source to drain.").detail("Holes are the weak carrier.", &["HOLE MOBILITY"]),
    Beat::new("paired with an NMOS", BEAT_MS).note("Together they make a CMOS inverter.", "The pair side by side.").detail("Power only on the flip.", &["INVERTER"]),
];
const S1_K: &[ChipKey] = &[
    ChipKey::at(DEV, 1000.0, 0.50, 0.35, PM).title("PMOS", "off: gate high"),
    ChipKey::at(DEV, 900.0, 0.45, 0.30, PON).title("on", "gate low, holes flow"),
    ChipKey::at(PAIR_VIEW, 1400.0, 0.40, 0.35, INV0).title("CMOS", "PMOS + NMOS"),
];

const S2_B: &[Beat] = &[
    Beat::new("p+ SOURCE", BEAT_MS).note("SiGe:B on the Vdd side.", "The source lights.").detail("Boron-doped SiGe.", &["p+ SOURCE"]),
    Beat::new("PMOS CHANNEL", BEAT_MS).note("Holes flow here when the gate is low.", "The channel lights; holes flow.").detail("Squeezed by the stressors.", &["PMOS CHANNEL"]),
    Beat::new("p+ DRAIN", BEAT_MS).note("SiGe:B, the output.", "The drain lights.").detail("Same stressor as the source.", &["p+ DRAIN"]),
    Beat::new("PMOS GATE", BEAT_MS).note("Metal gate on HfO2 with spacers.", "The gate lights.").detail("Its work function sets Vt.", &["PMOS GATE"]),
    Beat::new("N-WELL", BEAT_MS).note("n-type silicon tied to Vdd.", "The well lights.").detail("Reverse-biases the junctions.", &["N-WELL"]),
    Beat::new("SiGe STRESSOR and BORON DOPING", BEAT_MS).note("Regrown SiGe squeezes the channel; boron is grown in.", "Arrows and dopants light.").detail("Boron diffuses fast.", &["SiGe:B"]),
];
const S2_K: &[ChipKey] = &[
    ChipKey::at(DEV, 850.0, 0.30, 0.35, PM.spot(P::Source)).labels(&[(P::Source, "p+ source")]),
    ChipKey::at(DEV, 820.0, 0.40, 0.25, PON.spot(P::Channel)).labels(&[(P::Channel, "channel")]),
    ChipKey::at(DEV, 850.0, 0.70, 0.35, PM.spot(P::Drain)).labels(&[(P::Drain, "p+ drain")]),
    ChipKey::at(FIN, 700.0, 0.30, 0.25, ChipState { cut: 1.0, ..PM }.spot(P::Gate)).labels(&[(P::Gate, "gate")]),
    ChipKey::at(DEV, 950.0, 0.50, 0.15, PM.spot(P::Well)).labels(&[(P::Well, "n-well")]),
    ChipKey::at(DEV, 850.0, 0.50, 0.30, SIGE.spot(P::Dopants).spot(P::Channel)).labels(&[(P::Dopants, "SiGe:B"), (P::Channel, "squeezed")]),
];

const S3_B: &[Beat] = ZC_B;
const S3_K: &[ChipKey] = ZC_K;

const S4_B: &[Beat] = &[
    Beat::new("STD CELL: PMOS on top, NMOS below", BEAT_MS).note("A standard cell stacks a PMOS strip over an NMOS strip with a shared gate.", "A pair with its contacts.").detail("Thousands of cell types per library.", &["STD CELL"]),
    Beat::new("rails along the edges", BEAT_MS).note("Vdd and ground rails run along the top and bottom edges in metal.", "Metal rails appear over the pair.").detail("Cell height = tracks x metal-2 pitch.", &["9T, 7.5T (ASAP7)"]),
    Beat::new("TAP CELL and rows", BEAT_MS).note("Cells tile in rows; tap cells tie the wells to the rails to prevent latch-up.", "Pairs repeat in a row under the metal.").detail("7-8 tracks favour area, 11-12 speed.", &["TAP CELL"]),
];
const S4_K: &[ChipKey] = &[
    ChipKey::at(PAIR_VIEW, 1400.0, 0.40, 0.40, ChipState { vg: 0.5, inversion: 0.0, flow: 0.0, ..INV0 }).title("standard cell", "PMOS over NMOS"),
    ChipKey::at(STACK, 1900.0, 0.40, 0.40, ChipState { metal: 2.0, vg: 0.5, inversion: 0.0, flow: 0.0, ..INV0 }).labels(&[(P::ThinMetal, "rails")]).title("rails", "Vdd and ground"),
    ChipKey::at(STACK, 2600.0, 0.45, 0.35, ROW).title("rows", "tap cells tie the wells"),
];

const S5_B: &[Beat] = ZD_B;
const S5_K: &[ChipKey] = ZD_K;
const S6_B: &[Beat] = ZB_B;
const S6_K: &[ChipKey] = ZB_K;
const S7_B: &[Beat] = ZE_B;
const S7_K: &[ChipKey] = ZE_K;

const S8_B: &[Beat] = &[
    Beat::new("TSMC, Intel, Samsung: stressors in every node", BEAT_MS).note("The leading fabs build PMOS stressors into every FinFET and GAA node.", "A strained FinFET PMOS.").detail("TSM, INTC, Samsung.", &["Foundries"]),
    Beat::new("Applied Materials (AMAT): epi tools", BEAT_MS).note("The SiGe is grown in epitaxy tools; Applied had 53% of the epi market in 2004 per Gartner.", "Boron-doped SiGe in the source and drain.").detail("ASM International and Kokusai too.", &["AMAT epi"]),
    Beat::new("Synopsys, Cadence, Arm: cells and layout", BEAT_MS).note("Layout, place-and-route and cell libraries turn pairs into chips.", "Rows of standard cells with metal.").detail("SNPS, CDNS, ARM.", &["EDA and IP"]),
];
const S8_K: &[ChipKey] = &[
    ChipKey::at(FIN, 850.0, 0.40, 0.30, ChipState { arch: 1.0, ..SIGE }).title("foundries", "TSMC, Intel, Samsung"),
    ChipKey::at(DEV, 850.0, 0.45, 0.35, ChipState { dopants: 1.0, ..PM }).title("epitaxy", "Applied Materials"),
    ChipKey::at(STACK, 2600.0, 0.45, 0.35, ROW).title("cells and layout", "Synopsys, Cadence, Arm"),
];

const S9_B: &[Beat] = &[
    Beat::new("holes stay slow", BEAT_MS).note("Every node needs new strain or materials to keep the PMOS up.", "Holes crawl in an unstrained PMOS.").detail("The NMOS keeps the advantage.", &["Mobility gap"]),
    Beat::new("boron and germanium are hard", BEAT_MS).note("Boron diffusion and germanium oxide quality limit Ge-rich channels.", "Boron atoms near the channel.").detail("Research, not yet volume.", &["Ge channel"]),
    Beat::new("few epi vendors", BEAT_MS).note("Epitaxy tools come from few vendors; current shares are not public in the sources found.", "The SiGe source and drain.").detail("A tooling chokepoint.", &["Epi tools"]),
];
const S9_K: &[ChipKey] = &[
    ChipKey::at(DEV, 900.0, 0.45, 0.30, ChipState { flow: 0.4, ..PON }).title("slow holes", "the weaker carrier"),
    ChipKey::at(DEV, 820.0, 0.30, 0.25, ChipState { dopants: 1.0, halo: 0.6, ..PM }).title("boron, germanium", "diffusion and oxide"),
    ChipKey::at(DEV, 850.0, 0.50, 0.35, SIGE.spot(P::Source).spot(P::Drain)).title("epitaxy", "few tool vendors"),
];

const S: [SecData; 9] = [(S1_B, S1_K), (S2_B, S2_K), (S3_B, S3_K), (S4_B, S4_K), (S5_B, S5_K), (S6_B, S6_K), (S7_B, S7_K), (S8_B, S8_K), (S9_B, S9_K)];

chip_node!(ZOOMS, SECTIONS, Z, S);

pub static NODE: ChipNode = ChipNode { page: "PMOS", beats: BEATS, keys: KEYS, zooms: &ZOOMS, zoom_data: &Z, sections: &SECTIONS, section_data: &S };
