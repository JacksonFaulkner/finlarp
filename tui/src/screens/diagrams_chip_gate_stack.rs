// GATE STACK page (Chip tab): the high-k metal gate, in 3D on the Memory tab's
// template, always cut open at the front so the layers show. Overview: interlayer,
// high-k, work-function metal, fill, the replacement-gate flow, then the gate wrapping
// nanosheets. Zooms: a the layers, b gate-last flow, c EOT, d work-function metals,
// e GAA gaps. Sources: section 10 of CHIP_GATE_STACK.txt.

use super::diagrams_scene_chip::{chip_node, ChipNode, ChipState, SecData, ZoomData, BASE, BEAT_MS, FIN, OVERVIEW_MS, P};
use crate::ui::anim::Beat;
use poly3d::ChipKey;

const CUT: ChipState = ChipState { cut: 1.0, ..BASE };
const IL: ChipState = ChipState { hik: 0.0, ..CUT };
const HK: ChipState = ChipState { hik: 1.0, ..CUT };
const POLY: ChipState = ChipState { metal_gate: 0.0, hik: 0.0, ..CUT };
const ON: ChipState = ChipState { vg: 1.0, inversion: 1.0, depletion: 1.0, flow: 0.8, ..HK };
const GAA: ChipState = ChipState { arch: 2.0, ..HK };
const CLOSE: [f64; 3] = [0.0, 50.0, 60.0];

const BEATS: &[Beat] = &[
    Beat::new("the gate, cut open", OVERVIEW_MS)
        .note("The gate is a stack of thin films on the channel: an interlayer, high-k dielectric, work-function metal and a metal fill.", "The front of the gate is cut away to show its layers.")
        .detail("Each film is grown by ALD, one atomic layer per cycle.", &["Gate-last HKMG"]),
    Beat::new("IL GROWTH: half a nanometre of SiOx", OVERVIEW_MS)
        .note("A chemical oxide about 0.5 nm thick gives the high-k a clean interface to the silicon.", "A thin grey layer on the channel.")
        .detail("Its low k eats EOT budget.", &["IL ~0.5 nm"]),
    Beat::new("HIGH-K ALD: hafnium oxide", OVERVIEW_MS)
        .note("HfO2, about 1.5-2 nm, physically thicker than the SiO2 it replaced but electrically thinner.", "The dielectric thickens and turns bright yellow.")
        .detail("k ~20-25.", &["HfO2 1.5-2 nm", "EOT ~1 nm class"]),
    Beat::new("WORK-FUNCTION metal sets the threshold", OVERVIEW_MS)
        .note("TiN for PMOS, TiAlC for NMOS, with dipole caps: the metal's work function sets Vt.", "The gate turns to metal over the dielectric.")
        .detail("Multi-Vt comes from mixing layers.", &["TiN / TiAlC", "La / Al dipoles"]),
    Beat::new("METAL FILL and the field it applies", OVERVIEW_MS)
        .note("Tungsten fills the rest and is polished flat; a gate voltage now sets up the field that forms the channel.", "Field lines run down; the channel forms.")
        .detail("Fill sets gate resistance.", &["W fill"]),
    Beat::new("gate-last: a dummy poly gate first", OVERVIEW_MS)
        .note("The real stack goes in last: a polysilicon placeholder holds the place while the hot source/drain steps run.", "The gate turns back into brown polysilicon.")
        .detail("Then poly pull and replacement.", &["DUMMY POLY", "~1000 C anneal"]),
    Beat::new("in GAA, the stack must fit between sheets", OVERVIEW_MS)
        .note("Wrapping nanosheets, the IL, HfO2 and metal must all fit into gaps of a few nm.", "The channel splits into sheets with gate between them.")
        .detail("Variability in tiny gaps is the risk.", &["Gaps ~10 nm"]),
];
const KEYS: &[ChipKey] = &[
    ChipKey::at(FIN, 760.0, 0.25, 0.25, CUT).labels(&[(P::Gate, "metal gate"), (P::Oxide, "dielectric")]).notes(P::Gate, Some(P::Oxide)),
    ChipKey::at(CLOSE, 520.0, 0.20, 0.18, IL.spot(P::Oxide)).labels(&[(P::Oxide, "IL SiOx ~0.5 nm")]).notes(P::Oxide, Some(P::Channel)),
    ChipKey::at(CLOSE, 520.0, 0.25, 0.18, HK.spot(P::Oxide)).labels(&[(P::Oxide, "HfO2")]).notes(P::Oxide, Some(P::Gate)),
    ChipKey::at(CLOSE, 560.0, 0.30, 0.22, HK.spot(P::Gate)).labels(&[(P::Gate, "work-function metal")]).notes(P::Gate, Some(P::Oxide)),
    ChipKey::at(FIN, 700.0, 0.20, 0.22, ON).labels(&[(P::Gate, "W fill"), (P::Inversion, "channel")]).notes(P::Gate, Some(P::Inversion)),
    ChipKey::at(FIN, 760.0, 0.30, 0.28, POLY).labels(&[(P::Gate, "dummy poly")]).notes(P::Gate, Some(P::Source)),
    ChipKey::at(FIN, 700.0, 0.20, 0.20, GAA).labels(&[(P::Sheet, "sheets"), (P::Gate, "stack in the gaps")]).notes(P::Gate, Some(P::Sheet)),
];

const ZA_B: &[Beat] = &[
    Beat::new("IL and HfO2", BEAT_MS).note("A ~0.5 nm SiOx interlayer, then ~1.5-2 nm HfO2.", "The thin layers on the channel.").detail("HfO2 + dipole cap.", &["IL GROWTH", "HIGH-K ALD"]),
    Beat::new("TiN cap and work-function metals", BEAT_MS).note("A TiN cap protects during anneal; TiN (PMOS) or TiAlC(N) (NMOS) set Vt.", "The metal layers over the dielectric.").detail("Near the valence or conduction band.", &["TiN CAP", "WORK-FUNCTION"]),
    Beat::new("glue, barrier and W fill", BEAT_MS).note("TiN glue blocks tungsten diffusion; the W fill sets gate resistance.", "The full metal gate.").detail("U-shaped layers, fill in the middle.", &["METAL FILL"]),
];
const ZA_K: &[ChipKey] = &[
    ChipKey::at(CLOSE, 520.0, 0.22, 0.18, HK.spot(P::Oxide)).labels(&[(P::Oxide, "IL + HfO2")]).title("dielectric", "IL ~0.5 nm, HfO2 ~1.5-2 nm"),
    ChipKey::at(CLOSE, 560.0, 0.28, 0.20, ChipState { metal_gate: 0.7, ..HK }.spot(P::Gate)).labels(&[(P::Gate, "TiN / TiAlC")]).title("work-function metal", "sets Vt"),
    ChipKey::at(FIN, 700.0, 0.25, 0.22, HK.spot(P::Gate)).labels(&[(P::Gate, "W fill")]).title("fill", "gate resistance"),
];
const ZB_B: &[Beat] = &[
    Beat::new("DUMMY POLY", BEAT_MS).note("A poly placeholder gate goes on first.", "A brown polysilicon gate.").detail("Takes the heat for the real gate.", &["DUMMY POLY"]),
    Beat::new("SPACER + S/D, ILD + CMP", BEAT_MS).note("Spacers, source/drain implant and epi, a ~1000 C anneal, then oxide fill polished to the poly top.", "Source and drain glow with dopants.").detail("All hot steps done here.", &["~1000 C"]),
    Beat::new("POLY PULL and RMG STACK", BEAT_MS).note("The poly is etched out and the real stack grown in the trench, then filled and polished.", "The gate becomes metal on high-k.").detail("The stack never sees the heat.", &["POLY PULL", "RMG STACK"]),
];
const ZB_K: &[ChipKey] = &[
    ChipKey::at(FIN, 760.0, 0.30, 0.28, POLY).labels(&[(P::Gate, "dummy poly")]).title("dummy poly", "placeholder"),
    ChipKey::at(FIN, 780.0, 0.40, 0.30, ChipState { dopants: 1.0, ..POLY }).labels(&[(P::Dopants, "S/D, annealed")]).title("source/drain", "~1000 C anneal"),
    ChipKey::at(FIN, 740.0, 0.25, 0.25, HK).labels(&[(P::Gate, "replacement metal gate")]).title("poly pull, RMG", "stack goes in last"),
];
const ZC_B: &[Beat] = &[
    Beat::new("thin SiO2 leaks", BEAT_MS).note("Below ~1.2 nm, SiO2 leaks by direct tunnelling.", "Pink dots tunnel through a thin oxide.").detail("The 90 nm node hit the limit.", &["~1.2 nm limit"]),
    Beat::new("EOT: the SiO2 thickness with the same capacitance", BEAT_MS).note("EOT = t_hk x (3.9 / k_hk) + t_IL x (3.9 / k_IL): HfO2 can be thicker for the same EOT.", "The dielectric thickens; leakage stops.").detail("3.9 = k of SiO2.", &["EOT"]),
    Beat::new("Intel 45 nm: >10x less gate leakage", BEAT_MS).note("HfO2 at ~1.0 nm EOT: over 10x lower gate leakage and ~20% more drive (Intel claim).", "A thick high-k gate, on and conducting.").detail("Penryn, 2007.", &[">10x less leakage", "+20% drive"]),
];
const ZC_K: &[ChipKey] = &[
    ChipKey::at(CLOSE, 560.0, 0.25, 0.20, ChipState { leak: 1.0, metal_gate: 0.0, ..IL }).labels(&[(P::Oxide, "tunnelling")]).title("SiO2 limit", "~1.2 nm"),
    ChipKey::at(CLOSE, 540.0, 0.22, 0.18, HK.spot(P::Oxide)).labels(&[(P::Oxide, "thicker, same EOT")]).title("EOT", "t_hk x 3.9 / k"),
    ChipKey::at(FIN, 700.0, 0.25, 0.22, ON).labels(&[(P::Gate, "HKMG, 45 nm")]).title("Intel 45 nm", ">10x less leakage"),
];
const ZD_B: &[Beat] = &[
    Beat::new("NMOS WFM: TiAlC(N)", BEAT_MS).note("Al-rich metal near silicon's conduction band sets the NMOS threshold.", "An NMOS gate.").detail("La dipoles lower nFET Vt.", &["NMOS WFM TiAlC(N)"]),
    Beat::new("PMOS WFM: TiN", BEAT_MS).note("TiN near the valence band sets the PMOS threshold.", "A PMOS gate.").detail("Al dipoles raise pFET Vt.", &["PMOS WFM TiN"]),
    Beat::new("DIPOLE caps: many thresholds", BEAT_MS).note("Dipole caps and metal thickness give several Vt flavours per chip.", "An NMOS and PMOS side by side.").detail("Intel 18A: 4 NMOS + 4 PMOS Vt options.", &["DIPOLE"]),
];
const ZD_K: &[ChipKey] = &[
    ChipKey::at(FIN, 720.0, 0.25, 0.25, HK.spot(P::Gate)).labels(&[(P::Gate, "TiAlC(N)")]).title("NMOS work function", "near conduction band"),
    ChipKey::at(FIN, 720.0, 0.30, 0.25, ChipState { pmos: 1.0, ..HK }.spot(P::Gate)).labels(&[(P::Gate, "TiN")]).title("PMOS work function", "near valence band"),
    ChipKey::at([0.0, 60.0, 0.0], 1400.0, 0.35, 0.35, ChipState { pair: 1.0, cells: 2.0, ..HK }).labels(&[(P::Gate, "different metals")]).title("dipoles, multi-Vt", "18A: 4 + 4 options"),
];
const ZE_B: &[Beat] = &[
    Beat::new("sheets wrapped on four sides", BEAT_MS).note("In GAA the gate wraps every sheet.", "Sheets with gate between them.").detail("See GAA.", &["GAA gate"]),
    Beat::new("everything fits in the gap", BEAT_MS).note("IL, HfO2 and metal must all fit into gaps of a few nm.", "Close on the gaps between sheets.").detail("ALD into ~10 nm gaps.", &["Gaps"]),
    Beat::new("variability in tiny gaps", BEAT_MS).note("Small changes in layer thickness shift Vt sheet to sheet.", "Sheets conducting.").detail("The main GAA gate risk.", &["Vt variability"]),
];
const ZE_K: &[ChipKey] = &[
    ChipKey::at(FIN, 720.0, 0.20, 0.20, GAA).labels(&[(P::Sheet, "sheets")]).title("GAA gate", "all four sides"),
    ChipKey::at(CLOSE, 520.0, 0.18, 0.12, GAA.spot(P::Gate)).labels(&[(P::Gate, "stack in the gap")]).title("tight gaps", "a few nm"),
    ChipKey::at(FIN, 740.0, 0.30, 0.22, ChipState { vg: 1.0, inversion: 1.0, flow: 1.0, ..GAA }).labels(&[(P::Sheet, "Vt varies")]).title("variability", "sheet to sheet"),
];

const Z: [ZoomData; 5] = [
    ('a', "the layers, from interlayer to fill", ZA_B, ZA_K),
    ('b', "gate-last: dummy poly, pull, replace", ZB_B, ZB_K),
    ('c', "EOT: why the oxide had to go", ZC_B, ZC_K),
    ('d', "work-function metals and dipoles", ZD_B, ZD_K),
    ('e', "the stack in a nanosheet gap", ZE_B, ZE_K),
];

const S1_B: &[Beat] = &[
    Beat::new("a stack of films", BEAT_MS).note("Interlayer, high-k, work-function metal, fill.", "The gate cut open.").detail("All by ALD.", &["HKMG"]),
    Beat::new("dielectric", BEAT_MS).note("IL GROWTH then HIGH-K ALD.", "The dielectric lights.").detail("~0.5 + ~1.5-2 nm.", &["IL, HfO2"]),
    Beat::new("metal", BEAT_MS).note("TiN CAP, DIPOLE, WORK-FUNCTION, METAL FILL.", "The metal gate lights.").detail("Sets Vt and gate R.", &["Metal"]),
];
const S1_K: &[ChipKey] = &[
    ChipKey::at(FIN, 760.0, 0.25, 0.25, CUT).title("gate stack", "cut open"),
    ChipKey::at(CLOSE, 540.0, 0.22, 0.18, HK.spot(P::Oxide)).title("dielectric", "IL + HfO2"),
    ChipKey::at(CLOSE, 560.0, 0.28, 0.20, HK.spot(P::Gate)).title("metal", "WFM + fill"),
];
const S2_B: &[Beat] = ZB_B;
const S2_K: &[ChipKey] = ZB_K;
const S3_B: &[Beat] = ZA_B;
const S3_K: &[ChipKey] = ZA_K;
const S4_B: &[Beat] = &[
    Beat::new("GATE-FIRST: stack before the anneal", BEAT_MS).note("The stack goes in first and sees ~1000 C (IBM Common Platform, 32/28 nm).", "A metal gate, then dopants annealed around it.").detail("Vt shifts with heat.", &["GATE-FIRST"]),
    Beat::new("GATE-LAST: stack after", BEAT_MS).note("Dummy poly first; the stack added after the source/drain (Intel 45 nm, TSMC 28 nm).", "Poly, then metal.").detail("Never sees hot steps.", &["GATE-LAST"]),
    Beat::new("gate-last won", BEAT_MS).note("Gate-first was denser and simpler, but gate-last's stable Vt won as nodes shrank.", "A finished HKMG gate.").detail("Standard since 28 nm.", &["Gate-last"]),
];
const S4_K: &[ChipKey] = &[
    ChipKey::at(FIN, 760.0, 0.30, 0.28, ChipState { dopants: 1.0, ..HK }).title("gate-first", "high-k sees 1000 C"),
    ChipKey::at(FIN, 760.0, 0.30, 0.28, POLY).title("gate-last", "dummy poly first"),
    ChipKey::at(FIN, 740.0, 0.25, 0.25, ON).title("gate-last won", "stable Vt"),
];
const S5_B: &[Beat] = ZC_B;
const S5_K: &[ChipKey] = ZC_K;
const S6_B: &[Beat] = ZE_B;
const S6_K: &[ChipKey] = ZE_K;
const S7_B: &[Beat] = &[
    Beat::new("SiO2 limit and Intel 45 nm", BEAT_MS).note("~1.2 nm SiO2 limit; Intel 45 nm HfO2 at ~1.0 nm EOT, >10x less leakage, +20% drive.", "A thick high-k gate.").detail("Penryn, 2007.", &["45 nm HKMG"]),
    Beat::new("HfO2 k", BEAT_MS).note("k about 30 in one source, 20-25 in practice.", "The bright dielectric.").detail("vs 3.9 for SiO2.", &["k 20-25"]),
    Beat::new("ALD money", BEAT_MS).note("ASM 2025 revenue ~EUR 3.2B, margin 51.8%; single-wafer ALD $3.0B in 2024, $5.1-6.1B by 2030 (ASM).", "Sheets wrapped by ALD layers.").detail("Lam FY2025 $18.44B total.", &["ASM, Lam"]),
];
const S7_K: &[ChipKey] = &[
    ChipKey::at(FIN, 700.0, 0.25, 0.22, ON).title("45 nm HKMG", "~1.0 nm EOT"),
    ChipKey::at(CLOSE, 520.0, 0.22, 0.18, HK.spot(P::Oxide)).title("HfO2", "k 20-25"),
    ChipKey::at(FIN, 720.0, 0.20, 0.20, GAA).title("ALD market", "$3.0B (2024)"),
];
const S8_B: &[Beat] = &[
    Beat::new("ASM International (ASM.AS)", BEAT_MS).note("The ALD leader for the high-k films.", "The dielectric glows.").detail("Leading single-wafer ALD share (claim).", &["ASM"]),
    Beat::new("Applied Materials, Lam Research", BEAT_MS).note("Applied: Centura dielectric, Endura TiN. Lam: ALD tungsten, molybdenum for GAA.", "The metal layers.").detail("AMAT, LRCX.", &["AMAT, LRCX"]),
    Beat::new("Tokyo Electron, TSMC, Intel", BEAT_MS).note("TEL furnaces and ALD; TSMC and Intel integrate the stack.", "A finished gate, on.").detail("8035.T, TSM, INTC.", &["TEL, foundries"]),
];
const S8_K: &[ChipKey] = &[
    ChipKey::at(CLOSE, 540.0, 0.22, 0.18, HK.spot(P::Oxide)).title("ASM", "ALD high-k"),
    ChipKey::at(CLOSE, 560.0, 0.28, 0.20, HK.spot(P::Gate)).title("Applied, Lam", "metals, tungsten"),
    ChipKey::at(FIN, 700.0, 0.25, 0.22, ON).title("TEL, foundries", "integration"),
];
const S9_B: &[Beat] = &[
    Beat::new("Vt variability in GAA gaps", BEAT_MS).note("Tiny gaps make layer thickness, and so Vt, vary.", "Sheets with gate between.").detail("Sheet to sheet.", &["Variability"]),
    Beat::new("ALD uniformity, IL thickness", BEAT_MS).note("Every 0.1 nm of IL eats EOT; uniformity must hold across the wafer.", "The thin interlayer.").detail("Atomic control.", &["IL"]),
    Beat::new("fill voids", BEAT_MS).note("As gates shrink, the fill metal can leave voids.", "The metal fill.").detail("Raises gate resistance.", &["Voids"]),
];
const S9_K: &[ChipKey] = &[
    ChipKey::at(CLOSE, 520.0, 0.18, 0.12, GAA.spot(P::Gate)).title("variability", "tiny gaps"),
    ChipKey::at(CLOSE, 520.0, 0.20, 0.18, IL.spot(P::Oxide)).title("interlayer", "0.1 nm matters"),
    ChipKey::at(FIN, 700.0, 0.25, 0.22, HK.spot(P::Gate)).title("fill voids", "gate resistance"),
];

const S: [SecData; 9] = [(S1_B, S1_K), (S2_B, S2_K), (S3_B, S3_K), (S4_B, S4_K), (S5_B, S5_K), (S6_B, S6_K), (S7_B, S7_K), (S8_B, S8_K), (S9_B, S9_K)];

chip_node!(ZOOMS, SECTIONS, Z, S);

pub static NODE: ChipNode = ChipNode { page: "GATE STACK", beats: BEATS, keys: KEYS, zooms: &ZOOMS, zoom_data: &Z, sections: &SECTIONS, section_data: &S };
