// PLANAR page (Chip tab): the flat transistor of the planar era, in 3D on the Memory
// tab's template. Overview: Dennard shrinking, the four leak paths, short channels,
// strain and high-k metal gate, FD-SOI, then the hand-off to the fin. Zooms: a the four
// leaks, b DIBL, c high-k metal gate, d FD-SOI and body bias, e Dennard scaling.
// Sources: section 10 of CHIP_PLANAR.txt.

use super::diagrams_scene_chip::{chip_node, ChipNode, ChipState, SecData, ZoomData, BASE, BEAT_MS, DEV, FIN, OVERVIEW_MS, P};
use crate::ui::anim::Beat;
use poly3d::ChipKey;

const ON: ChipState = ChipState { vg: 0.9, vd: 0.6, inversion: 1.0, depletion: 1.0, flow: 1.0, ..BASE };
const BIG: ChipState = ChipState { gate_len: 1.6, ..ON };
const SMALL: ChipState = ChipState { gate_len: 0.6, ..ON };
const LEAKS: ChipState = ChipState { vd: 0.8, leak: 1.0, gate_len: 0.6, hik: 0.0, metal_gate: 0.0, ..BASE };
const STRAINED: ChipState = ChipState { strain: 1.0, dopants: 0.6, ..ON };
const HKMG: ChipState = ChipState { hik: 1.0, metal_gate: 1.0, cut: 1.0, ..ON };
const SOI: ChipState = ChipState { soi: 1.0, ..ON };

const BEATS: &[Beat] = &[
    Beat::new("a flat channel under a flat gate", OVERVIEW_MS)
        .note("The planar transistor: source and drain either side of a gate sitting on the silicon surface; the channel forms in a thin layer under it.", "A planar NMOS with a long gate, conducting.")
        .detail("Every chip was built this way until 22 nm.", &["Planar: to 28/22 nm"]),
    Beat::new("Dennard scaling: shrink everything, for free", OVERVIEW_MS)
        .note("Shrinking every dimension and the voltage by the same factor made gates faster at the same power density.", "The gate shrinks while the device keeps conducting.")
        .detail("Gates per area x k^2, power density x 1.", &["k ~1.4 per node", "Power density flat"]),
    Beat::new("the leakage wall: four paths when it should be off", OVERVIEW_MS)
        .note("Around 2005 the threshold could not fall further: off transistors leaked under the channel, through the oxide and across the junctions.", "A short gate, off, with leakage under the channel and up through the oxide.")
        .detail("Supply voltage stalled near 1 V.", &["Each 60 mV of Vt lost = 10x leakage"]),
    Beat::new("strained silicon: faster carriers", OVERVIEW_MS)
        .note("SiGe in the PMOS source/drain and nitride caps on the NMOS stretched or squeezed the channel to speed the carriers.", "Arrows push along the channel; carriers flow faster.")
        .detail("Intel 90 nm: PMOS +25% drive.", &["STRAINED SI (90 nm)"]),
    Beat::new("high-k metal gate: stop the oxide leaking", OVERVIEW_MS)
        .note("Hafnium oxide lets the gate dielectric be physically thicker, cutting tunnelling, and a metal gate sets the threshold.", "Cut open: a thick, bright high-k layer under a metal gate.")
        .detail("Gate-last arrived at 45-28 nm.", &["HIGH-K METAL GATE"]),
    Beat::new("FD-SOI: a thin film on buried oxide", OVERVIEW_MS)
        .note("Building the channel in a few-nm silicon film on a buried oxide blocks the leak path below and allows body bias.", "A pale buried-oxide layer appears under the device.")
        .detail("Soitec makes the wafers; GF ships 22FDX.", &["FD-SOI", "BODY BIAS"]),
    Beat::new("why planar ended: the fin takes over", OVERVIEW_MS)
        .note("A flat gate cannot cut off the path below the surface at short lengths, so the channel stood up into a fin.", "The channel rises into fins wrapped by the gate.")
        .detail("Mature nodes, 28 nm and up, still make most wafers.", &["Mature nodes: 36% of foundry revenue (2025)"]),
];
const KEYS: &[ChipKey] = &[
    ChipKey::at(DEV, 1000.0, 0.50, 0.35, BIG).labels(&[(P::Gate, "flat gate"), (P::Inversion, "channel at the surface")]).notes(P::Gate, Some(P::Inversion)),
    ChipKey::at(DEV, 950.0, 0.45, 0.35, SMALL).labels(&[(P::Gate, "shrunk by 1/k")]).notes(P::Gate, Some(P::Drift)),
    ChipKey::at(DEV, 900.0, 0.40, 0.22, LEAKS).labels(&[(P::Substrate, "under the channel"), (P::Oxide, "through the oxide")]).notes(P::Substrate, Some(P::Oxide)),
    ChipKey::at(DEV, 900.0, 0.50, 0.30, STRAINED).labels(&[(P::Channel, "strained channel")]).notes(P::Channel, Some(P::Drift)),
    ChipKey::at(FIN, 720.0, 0.25, 0.25, HKMG).labels(&[(P::Oxide, "HfO2"), (P::Gate, "metal gate")]).notes(P::Oxide, Some(P::Gate)),
    ChipKey::at(DEV, 950.0, 0.45, 0.18, SOI).labels(&[(P::Well, "buried oxide")]).notes(P::Well, Some(P::Drift)),
    ChipKey::at(FIN, 850.0, 0.35, 0.28, ChipState { arch: 1.0, ..ON }).labels(&[(P::Fin, "fins")]).notes(P::Fin, Some(P::Gate)),
];

const ZA_B: &[Beat] = &[
    Beat::new("subthreshold: drain to source below Vt", BEAT_MS).note("Below threshold the channel still passes a weak current.", "Faint carriers cross under the gate.").detail("Set by the swing and Vt.", &["Leak 1"]),
    Beat::new("gate tunnelling through thin oxide", BEAT_MS).note("Thin SiO2 lets carriers tunnel straight through the gate dielectric.", "Pink dots rise through the oxide.").detail("High-k fixed this.", &["Leak 2"]),
    Beat::new("punch-through and junction leakage", BEAT_MS).note("In short devices the depletion regions meet in the body; junctions leak too (GIDL).", "Carriers take the deep path under the channel.").detail("Halos and fins fight it.", &["Leak 3, leak 4"]),
];
const ZA_K: &[ChipKey] = &[
    ChipKey::at(DEV, 900.0, 0.40, 0.25, ChipState { vg: 0.2, vd: 0.8, leak: 0.6, ..BASE }).labels(&[(P::Drift, "subthreshold")]).title("leak 1", "subthreshold"),
    ChipKey::at(FIN, 720.0, 0.25, 0.25, ChipState { cut: 1.0, hik: 0.0, metal_gate: 0.0, leak: 1.0, ..BASE }).labels(&[(P::Oxide, "tunnelling")]).title("leak 2", "gate tunnelling"),
    ChipKey::at(DEV, 900.0, 0.45, 0.20, LEAKS).labels(&[(P::Substrate, "punch-through")]).title("leaks 3 and 4", "junction, punch-through"),
];

const ZB_B: &[Beat] = &[
    Beat::new("SHORT CHANNEL: the drain reaches the source", BEAT_MS).note("Shrink the gate and the drain's field meets the source barrier.", "A short gate with the drain biased.").detail("The gate loses control.", &["SHORT CHANNEL"]),
    Beat::new("DIBL: Vt falls with drain voltage", BEAT_MS).note("The drain lowers the barrier, so the threshold drops as drain voltage rises.", "Leakage grows with drain voltage.").detail("Vt roll-off.", &["DIBL"]),
    Beat::new("the swing floor", BEAT_MS).note("Swing can't go below about 60 mV/decade at room temperature; each 60 mV of Vt lost costs 10x leakage.", "A device barely off, leaking.").detail("More Cox, less Cdep pushes S toward the floor.", &["S >= 60 mV/dec at 300 K"]),
];
const ZB_K: &[ChipKey] = &[
    ChipKey::at(DEV, 900.0, 0.45, 0.30, ChipState { gate_len: 0.6, vd: 0.5, leak: 0.3, ..BASE }).labels(&[(P::Gate, "short gate")]).title("short channel", "drain meets source"),
    ChipKey::at(DEV, 880.0, 0.50, 0.28, ChipState { gate_len: 0.6, vd: 1.0, leak: 1.0, ..BASE }).labels(&[(P::Drain, "drain up, Vt down")]).title("DIBL", "Vt roll-off"),
    ChipKey::at(DEV, 900.0, 0.40, 0.25, ChipState { vg: 0.3, vd: 0.6, leak: 0.7, depletion: 1.0, ..BASE }).labels(&[(P::Depletion, "Cdep")]).title("swing floor", "60 mV/decade"),
];

const ZC_B: &[Beat] = &[
    Beat::new("polysilicon on SiON", BEAT_MS).note("The old gate: doped polysilicon on a thin oxynitride, which leaked by tunnelling as it thinned.", "Cut open: a brown poly gate on a thin layer.").detail("Poly also depletes at its bottom.", &["Poly / SiON"]),
    Beat::new("HfO2: thicker but electrically thinner", BEAT_MS).note("Hafnium oxide's high permittivity gives the same control from a physically thicker layer.", "The dielectric thickens and brightens.").detail("Tunnelling falls sharply.", &["HIGH-K"]),
    Beat::new("a metal gate sets Vt", BEAT_MS).note("A metal gate replaces poly; its work function sets the threshold, and gate-last flows arrived at 45-28 nm.", "The gate turns metal-grey.").detail("See the GATE STACK node.", &["HIGH-K METAL GATE"]),
];
const ZC_K: &[ChipKey] = &[
    ChipKey::at(FIN, 720.0, 0.25, 0.25, ChipState { cut: 1.0, hik: 0.0, metal_gate: 0.0, leak: 0.8, ..BASE }).labels(&[(P::Gate, "polysilicon"), (P::Oxide, "SiON")]).title("poly on SiON", "leaks as it thins"),
    ChipKey::at(FIN, 700.0, 0.20, 0.22, ChipState { cut: 1.0, hik: 1.0, metal_gate: 0.0, ..BASE }).labels(&[(P::Oxide, "HfO2")]).title("high-k", "physically thicker"),
    ChipKey::at(FIN, 700.0, 0.30, 0.25, HKMG).labels(&[(P::Gate, "metal gate")]).title("metal gate", "work function sets Vt"),
];

const ZD_B: &[Beat] = &[
    Beat::new("bulk: depletion reaches deep", BEAT_MS).note("In bulk silicon the depletion region and leak paths reach deep into the body.", "A bulk device with depletion and deep leakage.").detail("Random dopants vary Vt.", &["Bulk"]),
    Beat::new("FD-SOI: a thin film on buried oxide", BEAT_MS).note("A few-nm undoped film on a buried oxide holds no depletion charge; the BOX blocks the path below.", "The pale BOX layer appears; leakage stops.").detail("Soitec Smart Cut wafers.", &["FD-SOI", "SOITEC"]),
    Beat::new("body bias under the BOX", BEAT_MS).note("A voltage under the BOX tunes Vt after fabrication: fast when needed, low-leak when idle.", "The substrate under the BOX lights.").detail("GlobalFoundries 22FDX.", &["BODY BIAS"]),
];
const ZD_K: &[ChipKey] = &[
    ChipKey::at(DEV, 950.0, 0.45, 0.15, ChipState { vg: 0.4, vd: 0.8, depletion: 1.0, leak: 0.8, gate_len: 0.7, ..BASE }).labels(&[(P::Depletion, "deep depletion")]).title("bulk", "leak path below"),
    ChipKey::at(DEV, 950.0, 0.45, 0.15, ChipState { soi: 1.0, gate_len: 0.7, ..ON }).labels(&[(P::Well, "buried oxide")]).title("FD-SOI", "thin film on BOX"),
    ChipKey::at(DEV, 950.0, 0.55, 0.15, ChipState { soi: 1.0, gate_len: 0.7, ..ON }.spot(P::Substrate)).labels(&[(P::Substrate, "back bias")]).title("body bias", "tune Vt after fab"),
];

const ZE_B: &[Beat] = &[
    Beat::new("one node: shrink everything by 1/k", BEAT_MS).note("Scale dimensions and voltage by 1/k, about 0.7 per node.", "One transistor.").detail("k ~1.4.", &["DENNARD SCALING"]),
    Beat::new("twice the transistors, same power", BEAT_MS).note("Gates per area x k^2, power per gate x 1/k^2: power density stays flat.", "The gate shrinks and more transistors fill the row.").detail("Clock could rise ~1.4x per node.", &["Power density x 1"]),
    Beat::new("until Vt stopped scaling", BEAT_MS).note("Leakage grows exponentially as Vt falls, so voltage stalled near 1 V: more transistors at the same power meant dark silicon and multicore.", "Small transistors leaking.").detail("Mid-2000s.", &["LEAKAGE WALL"]),
];
const ZE_K: &[ChipKey] = &[
    ChipKey::at([0.0, 20.0, 0.0], 1600.0, 0.45, 0.40, BIG).title("Dennard scaling", "shrink by 1/k"),
    ChipKey::at([0.0, 20.0, 0.0], 1900.0, 0.40, 0.45, ChipState { cells: 3.0, ..SMALL }).title("k^2 more gates", "same power density"),
    ChipKey::at([0.0, 20.0, 0.0], 1900.0, 0.40, 0.40, ChipState { cells: 3.0, ..LEAKS }).title("the leakage wall", "Vdd stalls near 1 V"),
];

const Z: [ZoomData; 5] = [
    ('a', "the four leakage paths", ZA_B, ZA_K),
    ('b', "short channels and DIBL", ZB_B, ZB_K),
    ('c', "high-k metal gate", ZC_B, ZC_K),
    ('d', "FD-SOI and body bias", ZD_B, ZD_K),
    ('e', "Dennard scaling and its end", ZE_B, ZE_K),
];

const S1_B: &[Beat] = &[
    Beat::new("DENNARD SCALING", BEAT_MS).note("Shrinking was free for decades.", "A big planar device.").detail("Speed up, power density flat.", &["k ~1.4"]),
    Beat::new("the LEAKAGE WALL", BEAT_MS).note("Around 2005, Vt and voltage stopped scaling.", "A short device leaking.").detail("Vdd ~1 V.", &["Leakage"]),
    Beat::new("patched, then replaced", BEAT_MS).note("Strain, high-k metal gate and FD-SOI patched planar until the fin.", "The channel rises into fins.").detail("MATURE NODES still planar.", &["22/28 nm"]),
];
const S1_K: &[ChipKey] = &[
    ChipKey::at(DEV, 1000.0, 0.50, 0.35, BIG).title("free scaling", "Dennard"),
    ChipKey::at(DEV, 900.0, 0.40, 0.22, LEAKS).title("leakage wall", "~2005"),
    ChipKey::at(FIN, 850.0, 0.35, 0.28, ChipState { arch: 1.0, ..ON }).title("then the fin", "22 nm"),
];
const S2_B: &[Beat] = &[
    Beat::new("the cross-section", BEAT_MS).note("n+ source and drain, gate on a thin dielectric, p-type bulk shared by all.", "A planar NMOS conducting.").detail("Electrons in the inversion layer.", &["Planar bulk"]),
    Beat::new("off, it should block", BEAT_MS).note("With the gate low the channel is gone.", "The device off.").detail("But it leaks.", &["Off"]),
    Beat::new("four leak paths", BEAT_MS).note("Subthreshold, tunnelling, junction/GIDL and punch-through.", "Leakage under the channel and through the oxide.").detail("The gate sees only the top.", &["4 leaks"]),
];
const S2_K: &[ChipKey] = &[
    ChipKey::at(DEV, 950.0, 0.45, 0.30, ON).title("planar NMOS", "conducting"),
    ChipKey::at(DEV, 950.0, 0.45, 0.30, BASE).title("off", "no channel"),
    ChipKey::at(DEV, 900.0, 0.40, 0.22, LEAKS).title("leaking", "four paths"),
];
const S3_B: &[Beat] = ZB_B;
const S3_K: &[ChipKey] = ZB_K;
const S4_B: &[Beat] = &[
    Beat::new("STRAINED SI", BEAT_MS).note("SiGe squeezes PMOS channels; nitride caps stretch NMOS ones.", "Strain arrows on the channel.").detail("Intel 90 nm: PMOS +25%.", &["STRAINED SI"]),
    Beat::new("HIGH-K METAL GATE: the dielectric", BEAT_MS).note("HfO2 replaces SiON, cutting tunnelling.", "A thick bright dielectric.").detail("45-28 nm.", &["HfO2"]),
    Beat::new("HIGH-K METAL GATE: the metal", BEAT_MS).note("A metal gate replaces poly and sets Vt.", "The metal gate.").detail("Gate-last flows.", &["Metal gate"]),
];
const S4_K: &[ChipKey] = &[
    ChipKey::at(DEV, 900.0, 0.50, 0.30, STRAINED).title("strained silicon", "90 nm"),
    ChipKey::at(FIN, 700.0, 0.20, 0.22, ChipState { cut: 1.0, hik: 1.0, metal_gate: 0.0, ..ON }).title("high-k", "HfO2"),
    ChipKey::at(FIN, 700.0, 0.30, 0.25, HKMG).title("metal gate", "sets Vt"),
];
const S5_B: &[Beat] = &[
    Beat::new("MATURE NODES: 36% of foundry revenue", BEAT_MS).note("28 nm and above were 36% of pure-play foundry revenue in 2025, from 54% in 2021.", "Rows of planar transistors.").detail("Counterpoint.", &["MATURE NODES"]),
    Beat::new("UMC and GLOBALFOUNDRIES", BEAT_MS).note("UMC: 22/28 nm about 35-40% of 2025 revenue. GlobalFoundries: FDX, RF, auto; FY25 $6.79B.", "An FD-SOI device.").detail("UMC 2025 revenue NT$237.5B.", &["UMC", "GFS"]),
    Beat::new("SMIC", BEAT_MS).note("SMIC builds mostly 28 nm and above, for mature and domestic demand.", "Planar devices in a row.").detail("0981.HK.", &["SMIC"]),
];
const S5_K: &[ChipKey] = &[
    ChipKey::at([0.0, 20.0, 0.0], 1900.0, 0.40, 0.45, ChipState { cells: 3.0, ..ON }).title("mature nodes", "28 nm and above"),
    ChipKey::at(DEV, 950.0, 0.45, 0.18, SOI).title("UMC, GlobalFoundries", "22/28 nm, FDX"),
    ChipKey::at([0.0, 20.0, 0.0], 1900.0, 0.40, 0.45, ChipState { cells: 3.0, ..BIG }).title("SMIC", "28 nm and up"),
];
const S6_B: &[Beat] = ZE_B;
const S6_K: &[ChipKey] = ZE_K;
const S7_B: &[Beat] = ZD_B;
const S7_K: &[ChipKey] = ZD_K;
const S8_B: &[Beat] = &[
    Beat::new("TSMC and Intel", BEAT_MS).note("TSMC still runs a large 28 nm line; Intel shipped the first 22 nm FinFET in 2011.", "A planar device turning into a FinFET.").detail("TSM, INTC.", &["TSMC, Intel"]),
    Beat::new("UMC, GlobalFoundries, SMIC", BEAT_MS).note("The mature-node foundries ship most planar wafers.", "Rows of planar devices.").detail("UMC, GFS, 0981.HK.", &["Mature foundries"]),
    Beat::new("Soitec", BEAT_MS).note("Soitec makes the SOI wafers FD-SOI is built on.", "The buried oxide under the device.").detail("SOI.PA.", &["SOITEC"]),
];
const S8_K: &[ChipKey] = &[
    ChipKey::at(FIN, 850.0, 0.35, 0.28, ChipState { arch: 0.6, ..ON }).title("TSMC, Intel", "28 nm, first FinFET"),
    ChipKey::at([0.0, 20.0, 0.0], 1900.0, 0.40, 0.45, ChipState { cells: 3.0, ..ON }).title("UMC, GF, SMIC", "mature nodes"),
    ChipKey::at(DEV, 950.0, 0.45, 0.15, SOI).title("Soitec", "SOI wafers"),
];
const S9_B: &[Beat] = &[
    Beat::new("overcapacity", BEAT_MS).note("Mature-node overcapacity from China adds price pressure: UMC shipments +12.3% in 2025, revenue +2.3%.", "Rows of identical devices.").detail("Volume up, price down.", &["UMC 2025"]),
    Beat::new("FD-SOI stays niche", BEAT_MS).note("FD-SOI serves IoT, RF and automotive; the mass market moved to FinFET.", "An FD-SOI device.").detail("16/14 nm and below went FinFET.", &["Niche"]),
    Beat::new("node names", BEAT_MS).note("'N nm' labels no longer match any real gate length; compare by density instead.", "A shrinking gate.").detail("NODE NAME card.", &["Marketing names"]),
];
const S9_K: &[ChipKey] = &[
    ChipKey::at([0.0, 20.0, 0.0], 1900.0, 0.40, 0.45, ChipState { cells: 3.0, ..ON }).title("overcapacity", "price pressure"),
    ChipKey::at(DEV, 950.0, 0.45, 0.15, SOI).title("FD-SOI", "IoT, RF, auto"),
    ChipKey::at(DEV, 900.0, 0.45, 0.30, SMALL).title("node names", "not gate lengths"),
];

const S: [SecData; 9] = [(S1_B, S1_K), (S2_B, S2_K), (S3_B, S3_K), (S4_B, S4_K), (S5_B, S5_K), (S6_B, S6_K), (S7_B, S7_K), (S8_B, S8_K), (S9_B, S9_K)];

chip_node!(ZOOMS, SECTIONS, Z, S);

pub static NODE: ChipNode = ChipNode { page: "PLANAR", beats: BEATS, keys: KEYS, zooms: &ZOOMS, zoom_data: &Z, sections: &SECTIONS, section_data: &S };
