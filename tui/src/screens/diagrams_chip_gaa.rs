// GAA page (Chip tab): stacked nanosheets with the gate wrapped on all four sides, in
// 3D on the Memory tab's template. Overview: from the fin, the superlattice, release,
// gate fill, current through every sheet, sheet width, backside power. Zooms: a the
// process flow, b release, c sheet width, d backside power, e roadmap to CFET.
// Sources: section 10 of CHIP_GAA.txt.

use super::diagrams_scene_chip::{chip_node, ChipNode, ChipState, SecData, ZoomData, BASE, BEAT_MS, FIN, OVERVIEW_MS, P, STACK};
use crate::ui::anim::Beat;
use poly3d::ChipKey;

const G: ChipState = ChipState { arch: 2.0, cut: 1.0, ..BASE };
const STACKED: ChipState = ChipState { sige: 1.0, ..G };
const G_ON: ChipState = ChipState { vg: 0.9, vd: 0.6, inversion: 1.0, flow: 1.0, ..G };
const BACK: ChipState = ChipState { backside: 1.0, contacts: 1.0, metal: 3.0, signal: 1.0, ..G_ON };
const LOW: [f64; 3] = [0.0, -20.0, 40.0];

const BEATS: &[Beat] = &[
    Beat::new("start from the fin: three gated sides", OVERVIEW_MS)
        .note("A FinFET's gate wraps three sides of each fin; the bottom stays ungated.", "Two fins cut open under the gate.")
        .detail("Fins run out of room below 3 nm.", &["FinFET: 3 sides"]),
    Beat::new("a superlattice: Si and SiGe layers in each fin", OVERVIEW_MS)
        .note("Each fin is grown as alternating silicon and SiGe layers; the SiGe is sacrificial.", "The fins become stacks of silicon sheets with purple SiGe between.")
        .detail("3-4 Si/SiGe pairs, ~1 nm thickness control.", &["SUPERLATTICE"]),
    Beat::new("release: etch the SiGe out", OVERVIEW_MS)
        .note("After the source and drain are grown, the SiGe is etched sideways, leaving silicon sheets suspended.", "The SiGe between the sheets gives way.")
        .detail("Needs high Si:SiGe etch selectivity.", &["RELEASE"]),
    Beat::new("the gate fills every gap: four sides", OVERVIEW_MS)
        .note("High-k and metal go into the gaps by ALD, wrapping each sheet on all four sides.", "Gate metal fills between and under the sheets.")
        .detail("Gaps of about 10 nm must fit the whole stack.", &["HK/METAL GATE"]),
    Beat::new("current through every sheet", OVERVIEW_MS)
        .note("Gate on, every sheet conducts; the gate surrounds the channel, so leakage is lowest yet.", "Carriers stream through each sheet.")
        .detail("TSMC N2 vs N3E: +10-15% speed or -25-30% power.", &["Samsung SF3E, TSMC N2, Intel 18A"]),
    Beat::new("sheet width: drawn per device", OVERVIEW_MS)
        .note("Unlike fins, sheets can be drawn any width: wide for speed, narrow for density and low leakage.", "The sheets narrow down.")
        .detail("Weff ~ N x (W + 2T).", &["SHEET WIDTH"]),
    Beat::new("backside power: rails under the transistors", OVERVIEW_MS)
        .note("Power rails move under a thinned substrate, reached by nano-TSVs, leaving the front metal for signals.", "Copper rails appear beneath the device; metal stacks above.")
        .detail("Intel PowerVia on 18A; TSMC Super Power Rail on A16.", &["Backside power"]),
];
const KEYS: &[ChipKey] = &[
    ChipKey::at(FIN, 800.0, 0.25, 0.25, ChipState { arch: 1.0, cut: 1.0, ..BASE }).labels(&[(P::Fin, "fin: 3 sides")]).notes(P::Fin, Some(P::Gate)),
    ChipKey::at(FIN, 720.0, 0.20, 0.18, STACKED).labels(&[(P::Sheet, "Si sheets"), (P::Channel, "SiGe between")]).notes(P::Sheet, Some(P::Channel)),
    ChipKey::at(FIN, 700.0, 0.30, 0.20, ChipState { sige: 0.5, metal_gate: 0.2, ..G }).labels(&[(P::Sheet, "sheets released")]).notes(P::Sheet, Some(P::Source)),
    ChipKey::at(FIN, 700.0, 0.20, 0.20, G).labels(&[(P::Gate, "gate on all 4 sides")]).notes(P::Gate, Some(P::Sheet)),
    ChipKey::at(FIN, 760.0, 0.35, 0.25, G_ON).labels(&[(P::Sheet, "every sheet conducts")]).notes(P::Sheet, Some(P::Gate)),
    ChipKey::at(FIN, 760.0, 0.30, 0.25, ChipState { arch: 1.6, ..G_ON }).labels(&[(P::Sheet, "narrower sheets")]).notes(P::Sheet, None),
    ChipKey::at([0.0, 120.0, 0.0], 1700.0, 0.40, 0.22, BACK).labels(&[(P::TopMetal, "backside power rails"), (P::ThinMetal, "front: signals")]).notes(P::TopMetal, Some(P::ThinMetal)),
];

const ZA_B: &[Beat] = &[
    Beat::new("SUPERLATTICE and FIN PATTERN", BEAT_MS).note("Grow Si/SiGe layers, then etch them into fins.", "Striped fins.").detail("3-4 pairs.", &["SUPERLATTICE"]),
    Beat::new("DUMMY GATE, INNER SPACER, S/D EPI", BEAT_MS).note("A placeholder gate goes on, the SiGe ends are recessed and filled with nitride, and the source/drain grow from the sheet edges.", "The dummy gate and grown source/drain.").detail("Spacers isolate gate from S/D.", &["INNER SPACER", "S/D EPI"]),
    Beat::new("RELEASE and HK/METAL GATE", BEAT_MS).note("The dummy gate and SiGe come out; high-k and metal wrap every sheet.", "Gate metal fills the gaps.").detail("Replacement gate.", &["RELEASE", "HK/METAL GATE"]),
];
const ZA_K: &[ChipKey] = &[
    ChipKey::at(FIN, 720.0, 0.25, 0.20, ChipState { metal_gate: 0.0, ..STACKED }).labels(&[(P::Sheet, "superlattice")]).title("superlattice", "Si / SiGe pairs"),
    ChipKey::at(FIN, 720.0, 0.35, 0.22, ChipState { metal_gate: 0.0, dopants: 0.6, ..STACKED }).labels(&[(P::Gate, "dummy gate"), (P::Source, "S/D epi")]).title("dummy gate, spacers, epi", "build around the stack"),
    ChipKey::at(FIN, 700.0, 0.20, 0.20, G).labels(&[(P::Gate, "real gate")]).title("release, replace", "HK/metal wraps all"),
];
const ZB_B: &[Beat] = &[
    Beat::new("before release", BEAT_MS).note("Si sheets with sacrificial SiGe between.", "Purple SiGe in the gaps.").detail("SiGe sets the gap height.", &["Before"]),
    Beat::new("SiGe etched sideways", BEAT_MS).note("A selective etch removes SiGe and must not touch the silicon.", "The SiGe recedes.").detail("Any Si loss thins the sheet and shifts Vt.", &["Selectivity"]),
    Beat::new("gate metal takes its place", BEAT_MS).note("Where SiGe was, high-k and metal now wrap each sheet.", "Metal fills the gaps.").detail("ALD into ~10 nm gaps.", &["After"]),
];
const ZB_K: &[ChipKey] = &[
    ChipKey::at(FIN, 680.0, 0.20, 0.15, STACKED).labels(&[(P::Sheet, "Si sheets"), (P::Channel, "SiGe")]).title("before release", "sacrificial SiGe"),
    ChipKey::at(FIN, 680.0, 0.28, 0.18, ChipState { sige: 0.5, metal_gate: 0.2, ..G }).labels(&[(P::Sheet, "freed sheets")]).title("release", "selective SiGe etch"),
    ChipKey::at(FIN, 680.0, 0.20, 0.15, G).labels(&[(P::Gate, "metal in the gaps")]).title("after", "gate wraps 4 sides"),
];
const ZC_B: &[Beat] = &[
    Beat::new("FINFET: width in whole fins", BEAT_MS).note("A FinFET can only add fins.", "Narrow fins.").detail("Discrete steps.", &["FINFET"]),
    Beat::new("NANOSHEET: wide sheets for speed", BEAT_MS).note("Wide sheets give high drive for fast cells.", "Wide sheets.").detail("High-performance cells.", &["SHEET WIDTH"]),
    Beat::new("narrow sheets for density", BEAT_MS).note("Narrow sheets give low leakage and small cells, on the same chip.", "Narrow sheets.").detail("TSMC N2 mixes widths.", &["Weff ~ N(W + 2T)"]),
];
const ZC_K: &[ChipKey] = &[
    ChipKey::at(FIN, 760.0, 0.30, 0.25, ChipState { arch: 1.0, cut: 1.0, vg: 0.9, inversion: 1.0, flow: 1.0, ..BASE }).labels(&[(P::Fin, "fixed fins")]).title("FinFET", "whole fins"),
    ChipKey::at(FIN, 760.0, 0.30, 0.25, G_ON).labels(&[(P::Sheet, "wide sheets")]).title("wide sheets", "drive, speed"),
    ChipKey::at(FIN, 760.0, 0.30, 0.25, ChipState { arch: 1.5, ..G_ON }).labels(&[(P::Sheet, "narrow sheets")]).title("narrow sheets", "density, low leakage"),
];
const ZD_B: &[Beat] = &[
    Beat::new("front-side power: shared, crowded metal", BEAT_MS).note("Conventionally power and signals share the front metal, so power paths are long and thin.", "Metal stacked above the device.").detail("IR droop.", &["Frontside"]),
    Beat::new("rails move under the substrate", BEAT_MS).note("The wafer is thinned and power rails are built beneath, reached through nano-TSVs.", "Copper rails appear underneath.").detail("Short power path.", &["Backside rails"]),
    Beat::new("the front metal is all signals", BEAT_MS).note("Signals get the front metal to themselves: less congestion.", "Signals climb the front metal.").detail("PowerVia (18A), Super Power Rail (A16).", &["Intel 18A, TSMC A16"]),
];
const ZD_K: &[ChipKey] = &[
    ChipKey::at([0.0, 200.0, 0.0], 1700.0, 0.40, 0.30, ChipState { contacts: 1.0, metal: 4.0, ..G_ON }).labels(&[(P::ThinMetal, "power + signal")]).title("frontside power", "shared metal"),
    ChipKey::at(LOW, 1000.0, 0.40, -0.10, ChipState { backside: 1.0, contacts: 1.0, ..G_ON }).labels(&[(P::TopMetal, "backside rails"), (P::Via, "nano-TSV")]).title("backside power", "rails underneath"),
    ChipKey::at([0.0, 120.0, 0.0], 1700.0, 0.40, 0.22, BACK).labels(&[(P::ThinMetal, "signals only")]).title("front for signals", "less congestion"),
];
const ZE_B: &[Beat] = &[
    Beat::new("FINFET", BEAT_MS).note("Fins, three gated sides, to the 3 nm class.", "A FinFET.").detail("Intel 22 to TSMC N3.", &["FINFET"]),
    Beat::new("NANOSHEET", BEAT_MS).note("Stacked sheets, four sides: N2, 18A, SF2.", "Nanosheets.").detail("Now.", &["NANOSHEET"]),
    Beat::new("FORKSHEET and CFET", BEAT_MS).note("Forksheet puts a wall between n and p sheets (to A10); CFET stacks NMOS over PMOS (A7, after 2030).", "A CMOS pair of GAA devices.").detail("imec roadmap.", &["FORKSHEET", "CFET"]),
];
const ZE_K: &[ChipKey] = &[
    ChipKey::at(FIN, 800.0, 0.30, 0.28, ChipState { arch: 1.0, cut: 1.0, vg: 0.9, inversion: 1.0, flow: 1.0, ..BASE }).title("FinFET", "3 sides"),
    ChipKey::at(FIN, 760.0, 0.30, 0.25, G_ON).title("nanosheet", "4 sides"),
    ChipKey::at([0.0, 60.0, 0.0], 1400.0, 0.35, 0.35, ChipState { pair: 1.0, cells: 2.0, inv2: 1.0, flow2: 1.0, vg: 0.0, inversion: 0.0, flow: 0.0, ..G }).title("forksheet, CFET", "n and p ever closer"),
];

const Z: [ZoomData; 5] = [
    ('a', "the process flow: superlattice to gate", ZA_B, ZA_K),
    ('b', "release: etching out the SiGe", ZB_B, ZB_K),
    ('c', "sheet width: a new design knob", ZC_B, ZC_K),
    ('d', "backside power", ZD_B, ZD_K),
    ('e', "roadmap: nanosheet, forksheet, CFET", ZE_B, ZE_K),
];

const S1_B: &[Beat] = &[
    Beat::new("stack the sheets", BEAT_MS).note("Si/SiGe layers in each fin.", "Striped fins.").detail("SUPERLATTICE.", &["Stack"]),
    Beat::new("release them", BEAT_MS).note("Etch the SiGe out.", "Sheets freed.").detail("RELEASE.", &["Release"]),
    Beat::new("wrap the gate", BEAT_MS).note("Gate on all four sides.", "Metal fills the gaps; current flows.").detail("HK/METAL GATE.", &["Wrap"]),
];
const S1_K: &[ChipKey] = &[
    ChipKey::at(FIN, 720.0, 0.20, 0.18, STACKED).title("stack", "Si / SiGe"),
    ChipKey::at(FIN, 700.0, 0.30, 0.20, ChipState { sige: 0.5, metal_gate: 0.2, ..G }).title("release", "SiGe out"),
    ChipKey::at(FIN, 760.0, 0.35, 0.25, G_ON).title("wrap", "4 sides"),
];
const S2_B: &[Beat] = &[
    Beat::new("source and drain epi", BEAT_MS).note("SiP for NMOS, SiGeB for PMOS, grown from the sheet edges.", "The source and drain light.").detail("Strain and low contact R.", &["S/D EPI"]),
    Beat::new("the sheets", BEAT_MS).note("Current flows through each silicon sheet.", "The sheets light; carriers flow.").detail("3-4 sheets.", &["Sheets"]),
    Beat::new("gate and inner spacers", BEAT_MS).note("High-k and metal wrap each sheet; inner spacers isolate the gate from the source and drain.", "The gate lights.").detail("SiN or SiOCN spacers.", &["INNER SPACER"]),
];
const S2_K: &[ChipKey] = &[
    ChipKey::at(FIN, 800.0, 0.45, 0.30, ChipState { dopants: 1.0, ..G }.spot(P::Source).spot(P::Drain)).labels(&[(P::Source, "S/D epi")]),
    ChipKey::at(FIN, 740.0, 0.30, 0.22, G_ON.spot(P::Channel).spot(P::Sheet)).labels(&[(P::Sheet, "sheets")]),
    ChipKey::at(FIN, 720.0, 0.20, 0.20, G.spot(P::Gate).spot(P::Spacer)).labels(&[(P::Gate, "gate"), (P::Spacer, "spacers")]),
];
const S3_B: &[Beat] = ZB_B;
const S3_K: &[ChipKey] = ZB_K;
const S4_B: &[Beat] = ZA_B;
const S4_K: &[ChipKey] = ZA_K;
const S5_B: &[Beat] = ZC_B;
const S5_K: &[ChipKey] = ZC_K;
const S6_B: &[Beat] = ZD_B;
const S6_K: &[ChipKey] = ZD_K;
const S7_B: &[Beat] = &[
    Beat::new("Samsung SF3E: first GAA (2022)", BEAT_MS).note("vs 5 nm: -45% power, +23% performance, -16% area (vendor claim).", "Early nanosheets.").detail("SF3E.", &["Samsung 3GAA"]),
    Beat::new("TSMC N2 and Intel 18A (2025)", BEAT_MS).note("N2 vs N3E: +10-15% speed or -25-30% power. 18A vs Intel 3: ~25% frequency or -36% power.", "Nanosheets conducting.").detail("Vendor claims, not equal conditions.", &["N2", "18A"]),
    Beat::new("TSMC A16 (2026+)", BEAT_MS).note("Adds backside power: +8-10% speed, -15-20% power vs N2P.", "Backside rails under the device.").detail("Super Power Rail.", &["A16"]),
];
const S7_K: &[ChipKey] = &[
    ChipKey::at(FIN, 780.0, 0.30, 0.25, ChipState { gate_len: 1.1, ..G_ON }).title("SF3E", "2022"),
    ChipKey::at(FIN, 760.0, 0.35, 0.25, ChipState { gate_len: 0.9, ..G_ON }).title("N2, 18A", "2025"),
    ChipKey::at(LOW, 1000.0, 0.40, -0.10, ChipState { backside: 1.0, contacts: 1.0, ..G_ON }).title("A16", "backside power"),
];
const S8_B: &[Beat] = &[
    Beat::new("NODES: SF3, N2, 18A, A16", BEAT_MS).note("Samsung, TSMC and Intel all ship nanosheets.", "Nanosheets.").detail("Different names, same idea.", &["NODES"]),
    Beat::new("TOOLS: epi, ALD, selective etch", BEAT_MS).note("GAA raises tool spend: about $7B per 100K wafer starts a month vs $6B for FinFET (Applied).", "The superlattice and release.").detail("AMAT, LRCX, TEL, ASML.", &["TOOLS"]),
    Beat::new("roadmap", BEAT_MS).note("Forksheet then CFET extend the line past 2030 (imec).", "A CMOS pair.").detail("FORKSHEET, CFET.", &["imec"]),
];
const S8_K: &[ChipKey] = &[
    ChipKey::at(FIN, 760.0, 0.35, 0.25, G_ON).title("nodes", "SF3, N2, 18A, A16"),
    ChipKey::at(FIN, 720.0, 0.25, 0.20, STACKED).title("tools", "epi, ALD, etch"),
    ChipKey::at([0.0, 60.0, 0.0], 1400.0, 0.35, 0.35, ChipState { pair: 1.0, cells: 2.0, inv2: 1.0, flow2: 1.0, vg: 0.0, inversion: 0.0, flow: 0.0, ..G }).title("roadmap", "forksheet, CFET"),
];
const S9_B: &[Beat] = &[
    Beat::new("YIELD/COST: Samsung's ramp", BEAT_MS).note("Reported Samsung yields: SF3E 50-60%, SF3 ~20%, SF2 test ~30% (secondary reports).", "Nanosheets under a short gate.").detail("Not audited.", &["Samsung yields (reports)"]),
    Beat::new("TSMC N3E FinFET: ~82-86%", BEAT_MS).note("The FinFET it replaces yields far better (report).", "A FinFET.").detail("GAA resets the learning curve.", &["N3E ~82-86% (report)"]),
    Beat::new("wafer price", BEAT_MS).note("N2 wafers reported above $30,000 vs ~$18,000 for N3 (unconfirmed).", "A row of GAA devices.").detail("Cost per good die rises.", &["N2 >$30k (reported)"]),
];
const S9_K: &[ChipKey] = &[
    ChipKey::at(FIN, 760.0, 0.30, 0.25, ChipState { gate_len: 0.8, leak: 0.4, ..G_ON }).title("yield", "Samsung ramp"),
    ChipKey::at(FIN, 800.0, 0.30, 0.28, ChipState { arch: 1.0, cut: 1.0, vg: 0.9, inversion: 1.0, flow: 1.0, ..BASE }).title("FinFET yield", "~82-86% (report)"),
    ChipKey::at(STACK, 2400.0, 0.45, 0.35, ChipState { cells: 4.0, contacts: 1.0, metal: 3.0, ..G_ON }).title("wafer price", "N2 >$30k (reported)"),
];

const S: [SecData; 9] = [(S1_B, S1_K), (S2_B, S2_K), (S3_B, S3_K), (S4_B, S4_K), (S5_B, S5_K), (S6_B, S6_K), (S7_B, S7_K), (S8_B, S8_K), (S9_B, S9_K)];

chip_node!(ZOOMS, SECTIONS, Z, S);

pub static NODE: ChipNode = ChipNode { page: "GATE-ALL-AROUND", beats: BEATS, keys: KEYS, zooms: &ZOOMS, zoom_data: &Z, sections: &SECTIONS, section_data: &S };
