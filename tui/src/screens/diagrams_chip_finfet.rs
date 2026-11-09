// FINFET page (Chip tab): the channel stood up as fins with the gate wrapped over
// three sides, in 3D on the Memory tab's template. Overview: from planar, the fins
// rise, the gate wraps them, current flows in the fins, width comes in whole fins,
// sub-fin leakage, and a row of FinFETs under metal. Zooms: a fin formation, b gate
// wrap, c fin count, d FinFlex, e fin limits. Sources: section 10 of CHIP_FINFET.txt.

use super::diagrams_scene_chip::{chip_node, ChipNode, ChipState, SecData, ZoomData, BASE, BEAT_MS, FIN, OVERVIEW_MS, P, STACK};
use crate::ui::anim::Beat;
use poly3d::ChipKey;

const FF: ChipState = ChipState { arch: 1.0, ..BASE };
const FF_CUT: ChipState = ChipState { cut: 1.0, ..FF };
const FF_ON: ChipState = ChipState { vg: 0.9, vd: 0.6, inversion: 1.0, flow: 1.0, ..FF_CUT };
const SUBFIN: ChipState = ChipState { leak: 1.0, vd: 0.8, ..FF_CUT };
const ROW: ChipState = ChipState { cells: 4.0, contacts: 1.0, metal: 3.0, signal: 1.0, vg: 0.9, inversion: 1.0, flow: 0.8, ..FF };
const NOGATE: ChipState = ChipState { cut: 1.0, metal_gate: 1.0, hik: 0.0, ..FF };

const BEATS: &[Beat] = &[
    Beat::new("start from planar: a flat channel", OVERVIEW_MS)
        .note("A planar transistor gates the channel from the top only, and loses control as it shrinks.", "A planar device, cut open at the front.")
        .detail("Planar ran out at 22/28 nm.", &["1 gated side"]),
    Beat::new("stand the channel up as fins", OVERVIEW_MS)
        .note("Fins are etched from the silicon and oxide is etched back to expose them: the channel now stands up.", "The surface rises into two fins.")
        .detail("Patterned at a quarter of the litho pitch (SAQP).", &["FIN FORM, FIN REVEAL"]),
    Beat::new("the gate wraps three sides", OVERVIEW_MS)
        .note("High-k and the metal gate drape over the top and both sidewalls of every fin.", "Cut open: the gate fills down between the fins.")
        .detail("Weff per fin = 2 x Hfin + Wfin.", &["GATE WRAP: 3 sides"]),
    Beat::new("current flows up and down each fin", OVERVIEW_MS)
        .note("Gate on, the whole fin conducts: electrons run source to drain through every fin.", "Carriers stream through both fins.")
        .detail("The gate keeps control at short lengths.", &["Intel 22 nm tri-gate, 2011"]),
    Beat::new("width comes in whole fins", OVERVIEW_MS)
        .note("A FinFET can't be drawn any width: it is 1, 2 or 3 fins wide, so drive steps in whole fins.", "A third fin appears beside the two.")
        .detail("FinFlex on N3 mixes fin counts per block.", &["QUANTIZED W", "FIN COUNT 1-3"]),
    Beat::new("the bottom isn't gated: sub-fin leakage", OVERVIEW_MS)
        .note("Below the fin the gate has no grip; a punch-through-stop doping blocks most of the leak.", "Faint carriers sneak under the fins.")
        .detail("One reason fins hit limits below 3 nm.", &["Sub-fin leakage"]),
    Beat::new("rows of FinFETs: N16 to N3", OVERVIEW_MS)
        .note("From TSMC N16 to N3 the fin was stretched, not replaced; 7 nm and below were 74% of TSMC's 2025 wafer revenue.", "A row of FinFETs under contacts and metal.")
        .detail("Next: nanosheets (GAA) at N2.", &["N5: gate pitch 51 nm, fin pitch 28 nm", "N3: gate pitch 45 nm"]),
];
const KEYS: &[ChipKey] = &[
    ChipKey::at(FIN, 900.0, 0.35, 0.30, ChipState { cut: 1.0, ..BASE }).labels(&[(P::Channel, "flat channel"), (P::Gate, "gate on top")]).notes(P::Channel, Some(P::Gate)),
    ChipKey::at(FIN, 850.0, 0.30, 0.30, ChipState { cut: 1.0, metal_gate: 1.0, ..FF }).labels(&[(P::Fin, "fins")]).notes(P::Fin, Some(P::Sti)),
    ChipKey::at(FIN, 760.0, 0.20, 0.30, FF_CUT).labels(&[(P::Gate, "gate wraps 3 sides"), (P::Oxide, "high-k")]).notes(P::Gate, Some(P::Fin)),
    ChipKey::at(FIN, 760.0, 0.30, 0.30, FF_ON).labels(&[(P::Fin, "whole fin conducts")]).notes(P::Fin, Some(P::Gate)),
    ChipKey::at(FIN, 820.0, 0.25, 0.30, ChipState { fins: 3.0, ..FF_ON }).labels(&[(P::Fin, "a third fin")]).notes(P::Fin, Some(P::Channel)),
    ChipKey::at(FIN, 800.0, 0.30, 0.30, SUBFIN).labels(&[(P::Substrate, "sub-fin leakage")]).notes(P::Substrate, Some(P::Fin)),
    ChipKey::at(STACK, 2500.0, 0.45, 0.35, ROW).labels(&[(P::Gate, "FinFET rows"), (P::ThinMetal, "wiring")]).notes(P::Gate, Some(P::ThinMetal)),
];

const ZA_B: &[Beat] = &[
    Beat::new("SAQP: fins at a quarter of the litho pitch", BEAT_MS).note("Self-aligned quadruple patterning splits each printed line into four, so fins come out finer than lithography could print.", "The surface, about to rise.").detail("Spacers deposited and etched twice.", &["SAQP"]),
    Beat::new("FIN FORM: etch the silicon", BEAT_MS).note("Etching between the patterned lines leaves silicon fins standing.", "Fins rise from the surface.").detail("Tens of nm tall.", &["FIN FORM"]),
    Beat::new("FIN REVEAL: oxide fills and is etched back", BEAT_MS).note("Oxide fills between the fins and is recessed to expose their tops; the oxide isolates the fins below.", "The STI oxide sits around the fin bases.").detail("Reveal height sets the gated fin height.", &["FIN REVEAL"]),
];
const ZA_K: &[ChipKey] = &[
    ChipKey::at(FIN, 850.0, 0.30, 0.30, ChipState { cut: 1.0, ..BASE }).labels(&[(P::Channel, "silicon surface")]).title("SAQP", "4x pitch splitting"),
    ChipKey::at(FIN, 800.0, 0.25, 0.30, NOGATE).labels(&[(P::Fin, "etched fins")]).title("fin form", "etch the silicon"),
    ChipKey::at(FIN, 800.0, 0.35, 0.30, NOGATE.spot(P::Sti).spot(P::Fin)).labels(&[(P::Sti, "oxide, etched back"), (P::Fin, "revealed fin")]).title("fin reveal", "oxide recess"),
];
const ZB_B: &[Beat] = &[
    Beat::new("high-k over the fin", BEAT_MS).note("The dielectric coats the top and both sidewalls.", "The yellow dielectric over the fins.").detail("HfO2-based.", &["hi-k"]),
    Beat::new("metal fills around it", BEAT_MS).note("Work-function metal and fill metal wrap the fin on three sides.", "The gate fills between the fins.").detail("Weff = 2 x Hfin + Wfin per fin.", &["GATE WRAP"]),
    Beat::new("three gated sides, not four", BEAT_MS).note("The fin's bottom stays ungated: the gate controls far more than planar, but not everything.", "The gate on, carriers in the fins; faint leak below.").detail("GAA closes the fourth side.", &["3 sides"]),
];
const ZB_K: &[ChipKey] = &[
    ChipKey::at(FIN, 720.0, 0.20, 0.30, ChipState { hik: 1.0, ..FF_CUT }.spot(P::Oxide)).labels(&[(P::Oxide, "high-k on 3 sides")]).title("dielectric", "top and sidewalls"),
    ChipKey::at(FIN, 720.0, 0.15, 0.30, FF_CUT.spot(P::Gate)).labels(&[(P::Gate, "metal wraps the fin")]).title("gate wrap", "three sides"),
    ChipKey::at(FIN, 740.0, 0.30, 0.30, ChipState { leak: 0.4, ..FF_ON }).labels(&[(P::Fin, "gated"), (P::Substrate, "ungated bottom")]).title("not four sides", "sub-fin path"),
];
const ZC_B: &[Beat] = &[
    Beat::new("one fin", BEAT_MS).note("The smallest FinFET is one fin wide.", "A single fin.").detail("Dense, low drive.", &["1 fin"]),
    Beat::new("two fins", BEAT_MS).note("Two fins double the drive.", "Two fins.").detail("The common logic width.", &["2 fins"]),
    Beat::new("three fins", BEAT_MS).note("Three fins for high-speed cells.", "Three fins.").detail("Width is quantised.", &["QUANTIZED W"]),
];
const ZC_K: &[ChipKey] = &[
    ChipKey::at(FIN, 800.0, 0.25, 0.30, ChipState { fins: 1.0, ..FF_ON }).labels(&[(P::Fin, "1 fin")]).title("fin count 1", "low drive"),
    ChipKey::at(FIN, 800.0, 0.30, 0.30, ChipState { fins: 2.0, ..FF_ON }).labels(&[(P::Fin, "2 fins")]).title("fin count 2", "2x drive"),
    ChipKey::at(FIN, 820.0, 0.35, 0.30, ChipState { fins: 3.0, ..FF_ON }).labels(&[(P::Fin, "3 fins")]).title("fin count 3", "3x drive"),
];
const ZD_B: &[Beat] = &[
    Beat::new("FinFlex 3-2: speed", BEAT_MS).note("Blocks built from 3-fin and 2-fin cells, for the fastest logic.", "Three-fin transistors in a row.").detail("TSMC N3.", &["3-2 FIN"]),
    Beat::new("FinFlex 2-2: balanced", BEAT_MS).note("2-fin cells throughout.", "Two-fin transistors.").detail("All options are based on 2-fin cells.", &["2-2 FIN"]),
    Beat::new("FinFlex 2-1: low power, dense", BEAT_MS).note("2-fin plus 1-fin cells for the densest, lowest-power blocks; 0.64x-0.85x of N5's 2-2 area.", "One-fin transistors.").detail("Mixed on one die.", &["2-1 FIN", "0.64x-0.85x area (TSMC)"]),
];
const ZD_K: &[ChipKey] = &[
    ChipKey::at([0.0, 30.0, 0.0], 1900.0, 0.35, 0.45, ChipState { fins: 3.0, cells: 3.0, ..FF_ON }).title("FinFlex 3-2", "speed"),
    ChipKey::at([0.0, 30.0, 0.0], 1900.0, 0.40, 0.45, ChipState { fins: 2.0, cells: 3.0, ..FF_ON }).title("FinFlex 2-2", "balanced"),
    ChipKey::at([0.0, 30.0, 0.0], 1900.0, 0.45, 0.45, ChipState { fins: 1.0, cells: 3.0, ..FF_ON }).title("FinFlex 2-1", "low power, dense"),
];
const ZE_B: &[Beat] = &[
    Beat::new("FIN LIMITS: thinner and taller", BEAT_MS).note("To shrink, fins get thinner and taller: thin fins vary, tall fins bend and taper.", "Fins with a shorter gate.").detail("Textbook limits.", &["FIN LIMITS"]),
    Beat::new("LEAKAGE: sub-fin, GIDL, tunnelling", BEAT_MS).note("More leakage paths open as fins shrink.", "Leakage under and around the fins.").detail("The bottom stays ungated.", &["LEAKAGE"]),
    Beat::new("the answer: nanosheets", BEAT_MS).note("Splitting each fin into stacked sheets wrapped on all four sides: gate-all-around at N2.", "The fins split into sheets.").detail("Samsung at 3 nm already.", &["GAA"]),
];
const ZE_K: &[ChipKey] = &[
    ChipKey::at(FIN, 760.0, 0.30, 0.30, ChipState { gate_len: 0.6, ..FF_ON }).labels(&[(P::Fin, "thin, tall fin")]).title("fin limits", "variability, bending"),
    ChipKey::at(FIN, 780.0, 0.30, 0.30, ChipState { gate_len: 0.6, ..SUBFIN }).labels(&[(P::Substrate, "sub-fin, GIDL")]).title("leakage", "grows below 3 nm"),
    ChipKey::at(FIN, 760.0, 0.25, 0.30, ChipState { arch: 2.0, ..FF_ON }).labels(&[(P::Sheet, "stacked sheets")]).title("nanosheets", "GAA at N2"),
];

const Z: [ZoomData; 5] = [
    ('a', "making fins: SAQP, form, reveal", ZA_B, ZA_K),
    ('b', "the gate wraps three sides", ZB_B, ZB_K),
    ('c', "fin count: width in whole fins", ZC_B, ZC_K),
    ('d', "FinFlex on N3", ZD_B, ZD_K),
    ('e', "fin limits and what comes next", ZE_B, ZE_K),
];

const S1_B: &[Beat] = &[
    Beat::new("fins", BEAT_MS).note("The channel stands up as a fin.", "Fins rise.").detail("FIN FORM.", &["Fins"]),
    Beat::new("gate wrap", BEAT_MS).note("The gate wraps three sides.", "The gate fills around the fins.").detail("GATE WRAP.", &["3 sides"]),
    Beat::new("whole-fin widths", BEAT_MS).note("Width comes in fins: 1, 2 or 3.", "A third fin appears.").detail("QUANTIZED W.", &["FIN COUNT"]),
];
const S1_K: &[ChipKey] = &[
    ChipKey::at(FIN, 820.0, 0.30, 0.30, NOGATE).title("fins", "channel stands up"),
    ChipKey::at(FIN, 760.0, 0.20, 0.30, FF_CUT).title("gate wrap", "three sides"),
    ChipKey::at(FIN, 820.0, 0.30, 0.30, ChipState { fins: 3.0, ..FF_ON }).title("fin count", "1, 2 or 3"),
];
const S2_B: &[Beat] = &[
    Beat::new("the fin: Hfin and Wfin", BEAT_MS).note("Tens of nm tall, single-digit to ~10 nm wide.", "The fin stands lit.").detail("Weff = 2 Hfin + Wfin.", &["Fin"]),
    Beat::new("high-k and gate metal", BEAT_MS).note("Wrapping the top and both sidewalls.", "The gate and dielectric light.").detail("HfO2-based.", &["Gate"]),
    Beat::new("the ungated bottom", BEAT_MS).note("Sub-fin leakage, blocked by a punch-through stop under the STI.", "Leakage under the fins.").detail("Planar had one gated face, the fin three.", &["Sub-fin"]),
];
const S2_K: &[ChipKey] = &[
    ChipKey::at(FIN, 720.0, 0.25, 0.30, FF_CUT.spot(P::Fin)).labels(&[(P::Fin, "Hfin x Wfin")]),
    ChipKey::at(FIN, 720.0, 0.20, 0.30, FF_CUT.spot(P::Gate).spot(P::Oxide)).labels(&[(P::Gate, "gate metal"), (P::Oxide, "high-k")]),
    ChipKey::at(FIN, 780.0, 0.30, 0.30, SUBFIN).labels(&[(P::Substrate, "punch-through stop")]),
];
const S3_B: &[Beat] = &[
    Beat::new("INTEL 22 and TSMC 16", BEAT_MS).note("Intel's 22 nm tri-gate (2011) and TSMC's 16FF+ (2015) started the FinFET era.", "Early FinFETs, tall gate pitch.").detail("vs 20 nm planar.", &["2011, 2015"]),
    Beat::new("TSMC N7 and N5", BEAT_MS).note("Gate pitch 57 then 51 nm; fin pitch 30 then 28 nm.", "Tighter FinFET rows.").detail("N5 from A15 SEM.", &["N7 57/30 (est)", "N5 51/28"]),
    Beat::new("TSMC N3 and SAMSUNG", BEAT_MS).note("N3: gate pitch 45 nm with FinFlex. Samsung went to GAA at 3 nm.", "A FinFET turning into sheets.").detail("The fin stretched, not replaced.", &["N3 45 nm"]),
];
const S3_K: &[ChipKey] = &[
    ChipKey::at([0.0, 30.0, 0.0], 1800.0, 0.40, 0.40, ChipState { cells: 2.0, gate_len: 1.2, ..FF_ON }).title("22 nm, 16FF+", "2011, 2015"),
    ChipKey::at([0.0, 30.0, 0.0], 1900.0, 0.40, 0.45, ChipState { cells: 3.0, gate_len: 0.9, ..FF_ON }).title("N7, N5", "57 and 51 nm gate pitch"),
    ChipKey::at(FIN, 800.0, 0.30, 0.30, ChipState { arch: 1.5, gate_len: 0.8, ..FF_ON }).title("N3, Samsung 3 nm", "45 nm pitch; GAA"),
];
const S4_B: &[Beat] = &[
    Beat::new("N7: about 91 million transistors per mm2", BEAT_MS).note("TSMC N7 logic density is estimated at about 91.2 MTr/mm2.", "A FinFET row.").detail("WikiChip estimate.", &["N7 ~91.2 MTr/mm2"]),
    Beat::new("N5: about 138 MTr/mm2", BEAT_MS).note("N5 measured about 137.6-138.2 MTr/mm2 in Apple's A15.", "A denser row.").detail("Angstronomics SEM.", &["N5 ~138 MTr/mm2"]),
    Beat::new("N3: 1.6x N5", BEAT_MS).note("TSMC claims 1.6x logic density for N3E against N5.", "A denser row still.").detail("Claims blend cell types.", &["N3E 1.6x"]),
];
const S4_K: &[ChipKey] = &[
    ChipKey::at([0.0, 30.0, 0.0], 1900.0, 0.40, 0.45, ChipState { cells: 3.0, gate_len: 1.0, ..FF_ON }).title("N7", "~91 MTr/mm2"),
    ChipKey::at([0.0, 30.0, 0.0], 2100.0, 0.40, 0.45, ChipState { cells: 4.0, gate_len: 0.85, ..FF_ON }).title("N5", "~138 MTr/mm2"),
    ChipKey::at([0.0, 30.0, 0.0], 2300.0, 0.40, 0.45, ChipState { cells: 5.0, gate_len: 0.75, ..FF_ON }).title("N3", "1.6x N5"),
];
const S5_B: &[Beat] = ZD_B;
const S5_K: &[ChipKey] = ZD_K;
const S6_B: &[Beat] = &[
    Beat::new("7 nm and below: 74% of 2025", BEAT_MS).note("TSMC's FinFET nodes at 7 nm and below were 74% of its 2025 wafer revenue, up from 69%.", "Rows of FinFETs.").detail("Quarterly mix 73-77%.", &["2025: 74%"]),
    Beat::new("5 nm: about 35-37%", BEAT_MS).note("5 nm was the largest single node all year.", "A row of N5-like devices.").detail("Q4: 35%.", &["5 nm"]),
    Beat::new("3 nm: rising to 28%", BEAT_MS).note("3 nm rose from 22% in Q1 to 28% in Q4.", "A denser row.").detail("All FinFET.", &["3 nm Q4: 28%"]),
];
const S6_K: &[ChipKey] = &[
    ChipKey::at(STACK, 2500.0, 0.45, 0.35, ROW).title("7 nm and below", "74% of 2025"),
    ChipKey::at([0.0, 30.0, 0.0], 2100.0, 0.40, 0.45, ChipState { cells: 4.0, gate_len: 0.85, ..FF_ON }).title("5 nm", "~35%"),
    ChipKey::at([0.0, 30.0, 0.0], 2300.0, 0.40, 0.45, ChipState { cells: 5.0, gate_len: 0.75, ..FF_ON }).title("3 nm", "28% in Q4"),
];
const S7_B: &[Beat] = ZE_B;
const S7_K: &[ChipKey] = ZE_K;
const S8_B: &[Beat] = &[
    Beat::new("TSMC (TSM)", BEAT_MS).note("N16 to N3 for NVIDIA, Apple and AMD.", "A FinFET row.").detail("The volume leader.", &["TSMC"]),
    Beat::new("Intel (INTC), Samsung", BEAT_MS).note("Intel from 22 nm to Intel 3; Samsung from 14 nm.", "FinFETs.").detail("Both now moving to GAA.", &["Intel, Samsung"]),
    Beat::new("tool makers", BEAT_MS).note("SAQP and fin etch run on ASML, Applied Materials, Lam Research and Tokyo Electron tools.", "Fins being formed.").detail("AMAT, LRCX, TEL, ASML.", &["Tools"]),
];
const S8_K: &[ChipKey] = &[
    ChipKey::at(STACK, 2500.0, 0.45, 0.35, ROW).title("TSMC", "N16 to N3"),
    ChipKey::at(FIN, 800.0, 0.30, 0.30, FF_ON).title("Intel, Samsung", "22 nm, 14 nm onward"),
    ChipKey::at(FIN, 800.0, 0.25, 0.30, NOGATE).title("tools", "litho, etch, deposition"),
];
const S9_B: &[Beat] = &[
    Beat::new("out of room", BEAT_MS).note("Fins can't get thinner or taller much below 3 nm.", "Thin fins, short gate.").detail("GAA resets yields.", &["Fin limits"]),
    Beat::new("rising wafer cost", BEAT_MS).note("Each FinFET node costs more per wafer; TSMC prices are not public.", "A row of devices.").detail("Rumour ranges only.", &["Wafer cost"]),
    Beat::new("estimates, not specs", BEAT_MS).note("Several pitches here are WikiChip estimates; Intel 22 nm fin dimensions weren't confirmed.", "A FinFET cut open.").detail("Read with care.", &["Notes"]),
];
const S9_K: &[ChipKey] = &[
    ChipKey::at(FIN, 760.0, 0.30, 0.30, ChipState { gate_len: 0.6, ..FF_ON }).title("fin limits", "below 3 nm"),
    ChipKey::at([0.0, 30.0, 0.0], 2100.0, 0.40, 0.45, ChipState { cells: 4.0, ..FF_ON }).title("wafer cost", "rising every node"),
    ChipKey::at(FIN, 760.0, 0.20, 0.30, FF_CUT).title("estimates", "WikiChip, SEM"),
];

const S: [SecData; 9] = [(S1_B, S1_K), (S2_B, S2_K), (S3_B, S3_K), (S4_B, S4_K), (S5_B, S5_K), (S6_B, S6_K), (S7_B, S7_K), (S8_B, S8_K), (S9_B, S9_K)];

chip_node!(ZOOMS, SECTIONS, Z, S);

pub static NODE: ChipNode = ChipNode { page: "FINFET", beats: BEATS, keys: KEYS, zooms: &ZOOMS, zoom_data: &Z, sections: &SECTIONS, section_data: &S };
