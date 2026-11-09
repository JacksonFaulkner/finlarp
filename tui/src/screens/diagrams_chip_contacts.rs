// CONTACTS page (Chip tab): the middle of line, plugs from silicon up to M1, in 3D on
// the Memory tab's template. Overview: pre-clean and silicide, liner and tungsten fill,
// the plugs, M1 landing, a signal climbing, contact resistance, then a row wired up.
// Zooms: a the module flow, b contact types, c COAG and SAC cap, d contact resistance,
// e new metals. Sources: section 10 of CHIP_CONTACTS.txt.

use super::diagrams_scene_chip::{chip_node, ChipNode, ChipState, SecData, ZoomData, BASE, BEAT_MS, DEV, OVERVIEW_MS, P, STACK};
use crate::ui::anim::Beat;
use poly3d::ChipKey;

const FF: ChipState = ChipState { arch: 1.0, vg: 0.9, inversion: 1.0, flow: 0.6, ..BASE };
const SIL: ChipState = ChipState { silicide: 1.0, ..FF };
const HALF: ChipState = ChipState { contacts: 0.5, ..SIL };
const PLUGS: ChipState = ChipState { contacts: 1.0, ..SIL };
const M1: ChipState = ChipState { metal: 1.0, ..PLUGS };
const SIG: ChipState = ChipState { signal: 1.0, ..M1 };
const ROW: ChipState = ChipState { cells: 4.0, metal: 2.0, ..SIG };
const MOL: [f64; 3] = [0.0, 150.0, 0.0];

const BEATS: &[Beat] = &[
    Beat::new("the transistor, before it is wired", OVERVIEW_MS)
        .note("Contacts are the vertical plugs from the silicon up to the first metal: the middle of line.", "A FinFET with nothing above it yet.")
        .detail("After the transistor, before the wiring.", &["Middle of line"]),
    Beat::new("PRE-CLEAN and SILICIDE on the source and drain", OVERVIEW_MS)
        .note("Native oxide is etched off and a few nm of NiSi or TiSi formed on the source and drain epi.", "A thin dark silicide layer on the source and drain.")
        .detail("Its barrier height sets contact resistance.", &["NiSi 0.65-0.7 eV", "TiSi2 0.58 eV"]),
    Beat::new("LINER/BARRIER and W FILL", OVERVIEW_MS)
        .note("Holes are lined with a few nm of Ti/TiN and filled with tungsten from WF6 and H2.", "Plugs rise from the source, drain and gate.")
        .detail("The liner takes width that carries no current.", &["Ti/TiN few nm", "W fill"]),
    Beat::new("CMP: polished flat", OVERVIEW_MS)
        .note("Excess tungsten is polished off, stopping on the dielectric, leaving three plugs.", "Three finished tungsten plugs.")
        .detail("Source, drain and gate.", &["CMP"]),
    Beat::new("VIA0 / M1: the first metal lands", OVERVIEW_MS)
        .note("The first via and metal layer land on the plugs at a 30-40 nm pitch.", "Copper M1 wires appear over the plugs.")
        .detail("Now the transistor is wired.", &["M1 pitch 30-40 nm"]),
    Beat::new("a signal climbs: and meets resistance", OVERVIEW_MS)
        .note("Current climbs from the drain through silicide, plug and via. Plugs are ~15-20 nm wide, below tungsten's 19.1 nm mean free path.", "A signal runs up the plug and along M1.")
        .detail("Contact resistance is now a bottleneck.", &["W mean free path 19.1 nm"]),
    Beat::new("every transistor needs three", OVERVIEW_MS)
        .note("Billions of transistors, three plugs each: contact resistance erodes each node's gains.", "A row of transistors with plugs and wiring.")
        .detail("Intel 10 nm: cobalt and COAG.", &["TSMC N2: up to 20% MoL R+C cut (reported)"]),
];
const KEYS: &[ChipKey] = &[
    ChipKey::at(DEV, 1000.0, 0.45, 0.35, FF).labels(&[(P::Source, "source epi"), (P::Gate, "gate")]).notes(P::Source, Some(P::Gate)),
    ChipKey::at(DEV, 800.0, 0.40, 0.40, SIL.spot(P::Silicide)).labels(&[(P::Silicide, "silicide")]).notes(P::Silicide, Some(P::Source)),
    ChipKey::at(MOL, 1000.0, 0.40, 0.30, HALF).labels(&[(P::Contact, "W plugs rising")]).notes(P::Contact, Some(P::Silicide)),
    ChipKey::at(MOL, 1000.0, 0.50, 0.30, PLUGS).labels(&[(P::Contact, "three plugs")]).notes(P::Contact, None),
    ChipKey::at(MOL, 1100.0, 0.45, 0.35, M1).labels(&[(P::ThinMetal, "M1"), (P::Contact, "plugs")]).notes(P::ThinMetal, Some(P::Contact)),
    ChipKey::at(MOL, 1000.0, 0.35, 0.25, SIG).labels(&[(P::Contact, "resistance here")]).notes(P::Contact, Some(P::Silicide)),
    ChipKey::at(STACK, 2400.0, 0.45, 0.35, ROW).labels(&[(P::Contact, "3 per transistor")]).notes(P::Contact, Some(P::ThinMetal)),
];

const ZA_B: &[Beat] = &[
    Beat::new("PRE-CLEAN, SILICIDE", BEAT_MS).note("Etch the native oxide, form NiSi on the source and drain.", "The silicide layer forms.").detail("Ni/Ti anneal.", &["PRE-CLEAN", "SILICIDE"]),
    Beat::new("LINER/BARRIER, W FILL", BEAT_MS).note("Ti/TiN liner by ALD/CVD, then tungsten.", "Plugs rise.").detail("WF6 + H2.", &["LINER/BARRIER", "W FILL"]),
    Beat::new("CMP, VIA0 / M1", BEAT_MS).note("Polish flat, then the first via and metal land.", "M1 over the plugs.").detail("Stop on the ILD.", &["CMP", "VIA0 / M1"]),
];
const ZA_K: &[ChipKey] = &[
    ChipKey::at(DEV, 800.0, 0.40, 0.40, SIL.spot(P::Silicide)).labels(&[(P::Silicide, "NiSi")]).title("silicide", "pre-clean, Ni, anneal"),
    ChipKey::at(MOL, 1000.0, 0.40, 0.30, PLUGS.spot(P::Contact)).labels(&[(P::Contact, "liner + W")]).title("plugs", "liner, tungsten"),
    ChipKey::at(MOL, 1100.0, 0.45, 0.35, M1).labels(&[(P::ThinMetal, "M1")]).title("CMP, M1", "first metal lands"),
];
const ZB_B: &[Beat] = &[
    Beat::new("TRENCH CONTACT (TS)", BEAT_MS).note("A long bar strapping the source/drain epi.", "The source/drain plugs.").detail("Replaced single holes.", &["TS"]),
    Beat::new("GATE CONTACT", BEAT_MS).note("A plug on the gate metal.", "The gate plug lights.").detail("Used to sit off the active area.", &["GATE CONTACT"]),
    Beat::new("SELECTIVE W", BEAT_MS).note("Tungsten grown bottom-up: no seam, less barrier; >40% lower contact R (Applied claim).", "Plugs, cleaner.").detail("Vendor claim.", &["SELECTIVE W"]),
];
const ZB_K: &[ChipKey] = &[
    ChipKey::at(MOL, 1000.0, 0.40, 0.30, PLUGS.spot(P::Contact)).labels(&[(P::Source, "trench contact")]).title("trench contact", "strap on the epi"),
    ChipKey::at([0.0, 150.0, 70.0], 900.0, 0.20, 0.30, PLUGS.spot(P::Gate)).labels(&[(P::Gate, "gate contact")]).title("gate contact", "plug on the gate"),
    ChipKey::at(MOL, 1000.0, 0.50, 0.30, ChipState { signal: 1.0, ..PLUGS }).labels(&[(P::Contact, "bottom-up W")]).title("selective W", ">40% lower R (claim)"),
];
const ZC_B: &[Beat] = &[
    Beat::new("SAC CAP: a cap that forgives misalignment", BEAT_MS).note("A SiN cap on the gate lets source/drain contacts land close without shorting.", "The gate top lights.").detail("Self-aligned contact.", &["SAC CAP"]),
    Beat::new("COAG: contact over active gate", BEAT_MS).note("The gate contact lands right over the channel instead of beside it.", "The gate plug over the channel.").detail("Intel 10 nm.", &["COAG"]),
    Beat::new("smaller cells", BEAT_MS).note("COAG cut Intel's standard-cell height by about 10% (Intel claim, secondary).", "A tighter row.").detail("Area win.", &["~10% cell height"]),
];
const ZC_K: &[ChipKey] = &[
    ChipKey::at([0.0, 100.0, 60.0], 800.0, 0.25, 0.30, PLUGS.spot(P::Gate)).labels(&[(P::Gate, "SiN cap")]).title("SAC cap", "self-aligned"),
    ChipKey::at([0.0, 150.0, 70.0], 850.0, 0.15, 0.30, PLUGS.spot(P::Contact)).labels(&[(P::Contact, "over the active gate")]).title("COAG", "contact over active gate"),
    ChipKey::at(STACK, 2200.0, 0.45, 0.40, ChipState { cells: 4.0, ..PLUGS }).title("smaller cells", "~10% (Intel)"),
];
const ZD_B: &[Beat] = &[
    Beat::new("CONTACT RESISTANCE: rho_c / A", BEAT_MS).note("Contact area falls with pitch squared, so rho_c / A climbs fast.", "The silicide under a plug.").detail("pFET ~3e-9, nFET ~1e-8 ohm-cm2.", &["CONTACT RESISTANCE"]),
    Beat::new("LINER SQUEEZE", BEAT_MS).note("TiN doesn't shrink; in a 15 nm hole much of the width isn't conductor.", "A plug with a signal.").detail("Plug body R rises.", &["LINER SQUEEZE"]),
    Beat::new("BARRIER TUNING", BEAT_MS).note("Dopant segregation cuts the Schottky barrier from 0.7 to 0.34 eV.", "Current flows easily through the silicide.").detail("N2+ pre-silicide implant.", &["BARRIER TUNING"]),
];
const ZD_K: &[ChipKey] = &[
    ChipKey::at(DEV, 760.0, 0.40, 0.40, PLUGS.spot(P::Silicide)).labels(&[(P::Silicide, "rho_c / A")]).title("contact resistance", "climbs with pitch^2"),
    ChipKey::at(MOL, 900.0, 0.35, 0.25, ChipState { signal: 0.4, ..PLUGS }.spot(P::Contact)).labels(&[(P::Contact, "liner takes width")]).title("liner squeeze", "TiN doesn't shrink"),
    ChipKey::at(MOL, 950.0, 0.40, 0.28, SIG).labels(&[(P::Silicide, "0.7 -> 0.34 eV")]).title("barrier tuning", "dopant segregation"),
];
const ZE_B: &[Beat] = &[
    Beat::new("tungsten: the old standard", BEAT_MS).note("W ~5.6 uOhm-cm bulk, but its 19.1 nm mean free path hurts in 15 nm plugs.", "Tungsten plugs.").detail("Surface scattering.", &["W"]),
    Beat::new("cobalt: Intel 10 nm", BEAT_MS).note("Intel moved local interconnect to cobalt: 2x via resistance, 5-10x electromigration.", "Plugs carrying a signal.").detail("2017.", &["Co"]),
    Beat::new("Co / Ru / Mo", BEAT_MS).note("Ruthenium and molybdenum (~5.3 uOhm-cm) need thinner or no barriers.", "A row wired up.").detail("New tools, new qualification.", &["Co / Ru / Mo"]),
];
const ZE_K: &[ChipKey] = &[
    ChipKey::at(MOL, 1000.0, 0.40, 0.30, PLUGS).labels(&[(P::Contact, "W")]).title("tungsten", "5.6 uOhm-cm bulk"),
    ChipKey::at(MOL, 1000.0, 0.45, 0.30, SIG).labels(&[(P::Contact, "Co")]).title("cobalt", "Intel 10 nm"),
    ChipKey::at(STACK, 2300.0, 0.45, 0.35, ROW).labels(&[(P::Contact, "Ru, Mo")]).title("new metals", "Ru, Mo"),
];

const Z: [ZoomData; 5] = [
    ('a', "the contact module: silicide to M1", ZA_B, ZA_K),
    ('b', "contact types: trench, gate, selective W", ZB_B, ZB_K),
    ('c', "SAC cap and COAG", ZC_B, ZC_K),
    ('d', "contact resistance", ZD_B, ZD_K),
    ('e', "new metals: cobalt, ruthenium, molybdenum", ZE_B, ZE_K),
];

const S1_B: &[Beat] = &[
    Beat::new("silicide", BEAT_MS).note("NiSi on the source and drain.", "Silicide forms.").detail("SILICIDE.", &["NiSi"]),
    Beat::new("plugs", BEAT_MS).note("Liner and tungsten fill.", "Plugs rise.").detail("W FILL.", &["W"]),
    Beat::new("first metal", BEAT_MS).note("Via0 and M1 land on the plugs.", "M1 appears.").detail("VIA0 / M1.", &["M1"]),
];
const S1_K: &[ChipKey] = &[
    ChipKey::at(DEV, 800.0, 0.40, 0.40, SIL.spot(P::Silicide)).title("silicide", "pre-clean, NiSi"),
    ChipKey::at(MOL, 1000.0, 0.45, 0.30, PLUGS).title("plugs", "W fill"),
    ChipKey::at(MOL, 1100.0, 0.45, 0.35, SIG).title("M1", "wired"),
];
const S2_B: &[Beat] = &[
    Beat::new("M1 and via0", BEAT_MS).note("M1 wires at 30-40 nm pitch; via0 lands on a plug.", "M1 over the plugs.").detail("First wiring.", &["M1"]),
    Beat::new("plugs and the gate cap", BEAT_MS).note("Tungsten plugs with liners; a SiN cap on the gate.", "The plugs light.").detail("Self-aligned.", &["W plugs"]),
    Beat::new("silicide on the epi", BEAT_MS).note("NiSi or TiSi between plug and epi (>1e20 /cm3).", "The silicide lights.").detail("Barrier height sets R.", &["Silicide"]),
];
const S2_K: &[ChipKey] = &[
    ChipKey::at(MOL, 1100.0, 0.45, 0.35, M1.spot(P::ThinMetal)).labels(&[(P::ThinMetal, "M1")]),
    ChipKey::at(MOL, 1000.0, 0.40, 0.30, PLUGS.spot(P::Contact)).labels(&[(P::Contact, "W plug")]),
    ChipKey::at(DEV, 760.0, 0.40, 0.40, PLUGS.spot(P::Silicide)).labels(&[(P::Silicide, "NiSi / TiSi")]),
];
const S3_B: &[Beat] = &[
    Beat::new("TRENCH CONTACT and GATE CONTACT", BEAT_MS).note("A bar on the epi, a plug on the gate.", "Plugs on source, drain and gate.").detail("Self-aligned etch stops.", &["TS"]),
    Beat::new("COAG and SAC CAP", BEAT_MS).note("Contacts over the active gate, protected by a SiN cap.", "The gate plug over the channel.").detail("Intel 10 nm.", &["COAG"]),
    Beat::new("SELECTIVE W and Co / Ru / Mo", BEAT_MS).note("Bottom-up fill and new metals.", "Plugs carrying a signal.").detail("Less barrier.", &["New fills"]),
];
const S3_K: &[ChipKey] = &[
    ChipKey::at(MOL, 1000.0, 0.40, 0.30, PLUGS.spot(P::Contact)).title("trench and gate contacts", "three plugs"),
    ChipKey::at([0.0, 150.0, 70.0], 850.0, 0.15, 0.30, PLUGS.spot(P::Gate)).title("COAG, SAC cap", "over the active gate"),
    ChipKey::at(MOL, 1000.0, 0.45, 0.30, SIG).title("selective W, new metals", "less barrier"),
];
const S4_B: &[Beat] = ZD_B;
const S4_K: &[ChipKey] = ZD_K;
const S5_B: &[Beat] = &[
    Beat::new("W mean free path 19.1 nm", BEAT_MS).note("Wider than the plug, so surfaces scatter electrons.", "A tungsten plug.").detail("PRB 2012.", &["19.1 nm"]),
    Beat::new("Schottky barriers", BEAT_MS).note("NiSi 0.65-0.7 eV, TiSi2 0.58 eV; implant tuning to 0.34 eV.", "The silicide.").detail("Patents.", &["0.7 -> 0.34 eV"]),
    Beat::new("vendor and fab claims", BEAT_MS).note("Applied Volta W: up to 90% lower R (claim). Intel cobalt: 5-10x electromigration. TSMC N2: up to 20% MoL R+C cut.", "A wired row.").detail("Claims, not equal conditions.", &["Claims"]),
];
const S5_K: &[ChipKey] = &[
    ChipKey::at(MOL, 900.0, 0.35, 0.25, PLUGS.spot(P::Contact)).title("19.1 nm", "W mean free path"),
    ChipKey::at(DEV, 760.0, 0.40, 0.40, PLUGS.spot(P::Silicide)).title("barriers", "0.58-0.7 eV"),
    ChipKey::at(STACK, 2300.0, 0.45, 0.35, ROW).title("claims", "Applied, Intel, TSMC"),
];
const S6_B: &[Beat] = &[
    Beat::new("Applied: $28.37B in FY2025", BEAT_MS).note("Semiconductor Systems 73%, Global Services 23%, other 4%.", "Plugs and M1.").detail("10-K.", &["AMAT FY2025"]),
    Beat::new("Semi Systems: $20.80B", BEAT_MS).note("67% foundry/logic/other, 26% DRAM, 7% NAND.", "A row of transistors.").detail("Contacts are a logic specialty.", &["Mix"]),
    Beat::new("contact metals", BEAT_MS).note("Endura PVD/CVD/ALD, cobalt, selective W, molybdenum.", "Plugs with a signal.").detail("AMAT.", &["Endura"]),
];
const S6_K: &[ChipKey] = &[
    ChipKey::at(MOL, 1100.0, 0.45, 0.35, M1).title("Applied Materials", "$28.37B FY2025"),
    ChipKey::at(STACK, 2300.0, 0.45, 0.35, ROW).title("Semi Systems", "$20.80B"),
    ChipKey::at(MOL, 1000.0, 0.45, 0.30, SIG).title("contact metals", "Endura"),
];
const S7_B: &[Beat] = ZE_B;
const S7_K: &[ChipKey] = ZE_K;
const S8_B: &[Beat] = &[
    Beat::new("Applied Materials and Lam Research", BEAT_MS).note("Applied Endura; Lam ALTUS tungsten and molybdenum (FY2025 $18.44B).", "Plugs.").detail("AMAT, LRCX.", &["Tools"]),
    Beat::new("TSMC and Intel design the scheme", BEAT_MS).note("Intel first with cobalt and COAG at 10 nm.", "Plugs over the active gate.").detail("TSM, INTC.", &["Foundries"]),
    Beat::new("memory makers, TEL, EDA", BEAT_MS).note("Samsung, SK hynix, Micron buy the tools; TEL sells CVD/ALD; Synopsys and Cadence extract RC.", "A wired row.").detail("8035.T, SNPS, CDNS.", &["Others"]),
];
const S8_K: &[ChipKey] = &[
    ChipKey::at(MOL, 1000.0, 0.40, 0.30, PLUGS).title("Applied, Lam", "deposition"),
    ChipKey::at([0.0, 150.0, 70.0], 850.0, 0.15, 0.30, PLUGS.spot(P::Gate)).title("TSMC, Intel", "contact scheme"),
    ChipKey::at(STACK, 2300.0, 0.45, 0.35, ROW).title("buyers, EDA", "memory makers, TEL"),
];
const S9_B: &[Beat] = &[
    Beat::new("new metals need new tools", BEAT_MS).note("Mo and Ru need new tools and qualification.", "Plugs.").detail("Adoption risk.", &["Mo, Ru"]),
    Beat::new("barrierless fill", BEAT_MS).note("Dropping the barrier saves width but raises adhesion and diffusion risk.", "A plug with a signal.").detail("Reliability.", &["Barrierless"]),
    Beat::new("RC eats the node gain", BEAT_MS).note("Contact RC erodes node-to-node performance gains.", "A wired row.").detail("The middle of line matters.", &["Contact RC"]),
];
const S9_K: &[ChipKey] = &[
    ChipKey::at(MOL, 1000.0, 0.40, 0.30, PLUGS.spot(P::Contact)).title("new metals", "new tools"),
    ChipKey::at(MOL, 900.0, 0.35, 0.25, SIG.spot(P::Contact)).title("barrierless", "adhesion, diffusion"),
    ChipKey::at(STACK, 2300.0, 0.45, 0.35, ROW).title("contact RC", "erodes gains"),
];

const S: [SecData; 9] = [(S1_B, S1_K), (S2_B, S2_K), (S3_B, S3_K), (S4_B, S4_K), (S5_B, S5_K), (S6_B, S6_K), (S7_B, S7_K), (S8_B, S8_K), (S9_B, S9_K)];

chip_node!(ZOOMS, SECTIONS, Z, S);

pub static NODE: ChipNode = ChipNode { page: "CONTACTS", beats: BEATS, keys: KEYS, zooms: &ZOOMS, zoom_data: &Z, sections: &SECTIONS, section_data: &S };
