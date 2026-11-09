// THIN METAL, MID METAL and TOP METAL pages (Chip tab): the wiring stack over the
// transistors, in 3D on the Memory tab's template. All three share one stack (2 thin,
// 2 intermediate, 2 thick levels) and differ in where the camera goes and what lights.
// Sources: section 10 of CHIP_THIN_METAL.txt, CHIP_MID_METAL.txt, CHIP_TOP_METAL.txt.

use super::diagrams_scene_chip::{chip_node, ChipNode, ChipState, SecData, ZoomData, BASE, BEAT_MS, OVERVIEW_MS, P, STACK};
use crate::ui::anim::Beat;
use poly3d::ChipKey;

const DEVS: ChipState = ChipState { arch: 1.0, cells: 3.0, contacts: 1.0, vg: 0.9, inversion: 1.0, flow: 0.6, ..BASE };
const M0: ChipState = DEVS;
const M2: ChipState = ChipState { metal: 2.0, ..DEVS };
const M4: ChipState = ChipState { metal: 4.0, ..DEVS };
const M6: ChipState = ChipState { metal: 6.0, ..DEVS };
const SIG: ChipState = ChipState { signal: 1.0, ..M6 };
const EXP: ChipState = ChipState { explode: 1.0, ..M6 };
const THIN: [f64; 3] = [0.0, 280.0, 0.0];
const MID: [f64; 3] = [0.0, 400.0, 0.0];
const TOP: [f64; 3] = [0.0, 580.0, 0.0];

// ---------------------------------------------------------------- THIN METAL

const T_BEATS: &[Beat] = &[
    Beat::new("transistors with contacts, waiting for wires", OVERVIEW_MS)
        .note("Above the contacts, wiring levels connect transistor to transistor. The first four, M1-M4, are the thinnest.", "A row of transistors with tungsten plugs.").detail("Each level is one damascene loop.", &["M1-M4: 20-40 nm pitch"]),
    Beat::new("M1: the first copper level", OVERVIEW_MS)
        .note("Trench etched in low-k, lined with a 1-2 nm barrier, filled with copper, polished flat.", "Thin copper lines appear over the plugs.").detail("M1 pitch tracks the standard-cell pitch.", &["EUV ~26-30 nm, or 193i multi"]),
    Beat::new("M2 runs the other way", OVERVIEW_MS)
        .note("Alternate levels run perpendicular, joined by vias.", "A second thin level crosses the first.").detail("Via to the next level after a cap.", &["CAP + VIA"]),
    Beat::new("only the core is copper", OVERVIEW_MS)
        .note("A fixed 1-2 nm barrier skin lines every line; at 12-15 nm width it takes a big share of the cross-section.", "Close on the thin lines.").detail("The barrier doesn't scale down.", &["Line ~12-15 nm after barrier"]),
    Beat::new("signals cell to cell", OVERVIEW_MS)
        .note("A signal climbs a contact and runs along M1 to the next cell.", "Yellow pulses run up and along the thin metal.").detail("RC of thin wires now beats gate delay.", &["RC dominates"]),
    Beat::new("the stack continues up", OVERVIEW_MS)
        .note("Above M1-M4 the levels get thicker and wider, because RC falls with cross-section.", "Thicker levels stack above.").detail("See MID METAL and TOP METAL.", &["M5-M9, M10-M14"]),
    Beat::new("pulled apart: level by level", OVERVIEW_MS)
        .note("Exploded, the stack shows each level and its vias; the thin ones sit just above the transistors.", "The levels separate.").detail("Ru and Mo may replace copper in the thinnest.", &["TSMC N3E: 23 nm min pitch"]),
];
const T_KEYS: &[ChipKey] = &[
    ChipKey::at([0.0, 120.0, 0.0], 1800.0, 0.45, 0.40, M0).labels(&[(P::Contact, "contacts")]).notes(P::Contact, Some(P::Gate)),
    ChipKey::at(THIN, 1700.0, 0.40, 0.45, ChipState { metal: 1.0, ..DEVS }.spot(P::ThinMetal)).labels(&[(P::ThinMetal, "M1")]).notes(P::ThinMetal, Some(P::Contact)),
    ChipKey::at(THIN, 1700.0, 0.55, 0.45, M2.spot(P::ThinMetal).spot(P::Via)).labels(&[(P::ThinMetal, "M2, perpendicular"), (P::Via, "via")]).notes(P::ThinMetal, Some(P::Via)),
    ChipKey::at(THIN, 800.0, 0.35, 0.30, M2.spot(P::ThinMetal)).labels(&[(P::ThinMetal, "barrier + copper core")]).notes(P::ThinMetal, None),
    ChipKey::at(THIN, 1700.0, 0.45, 0.40, ChipState { signal: 1.0, ..M2 }).labels(&[(P::ThinMetal, "signal path")]).notes(P::ThinMetal, Some(P::Contact)),
    ChipKey::at(STACK, 2300.0, 0.45, 0.35, M6.spot(P::ThinMetal)).labels(&[(P::ThinMetal, "M1-M4"), (P::TopMetal, "thicker above")]).notes(P::ThinMetal, Some(P::TopMetal)),
    ChipKey::at([0.0, 450.0, 0.0], 2700.0, 0.45, 0.30, EXP.spot(P::ThinMetal)).labels(&[(P::ThinMetal, "thin levels")]).notes(P::ThinMetal, Some(P::Via)),
];

const TA_B: &[Beat] = &[
    Beat::new("LITHO PITCH and TRENCH ETCH", BEAT_MS).note("Print the pattern (EUV 26-30 nm or 193i multi) and cut trenches in low-k.", "The level about to form.").detail("Hard mask.", &["LITHO PITCH", "TRENCH ETCH"]),
    Beat::new("BARRIER+LINER and FILL METAL", BEAT_MS).note("Ta/TaN plus Co or Ru, 1-2 nm, then copper (or Ru, Mo).", "Copper lines fill in.").detail("Plate or reflow.", &["BARRIER+LINER", "FILL METAL"]),
    Beat::new("CMP and CAP + VIA", BEAT_MS).note("Polish flat, cap, and open the via to the next level.", "The next level crosses over with vias.").detail("Repeat for M2-M4.", &["CMP", "CAP + VIA"]),
];
const TA_K: &[ChipKey] = &[
    ChipKey::at(THIN, 1700.0, 0.40, 0.45, M0).title("litho and etch", "26-30 nm pitch"),
    ChipKey::at(THIN, 1700.0, 0.45, 0.45, ChipState { metal: 1.0, ..DEVS }.spot(P::ThinMetal)).labels(&[(P::ThinMetal, "Cu fill")]).title("liner and fill", "1-2 nm barrier"),
    ChipKey::at(THIN, 1700.0, 0.50, 0.45, M2.spot(P::Via)).labels(&[(P::Via, "via up")]).title("CMP, cap, via", "next level"),
];
const TB_B: &[Beat] = &[
    Beat::new("COPPER LINE: core only", BEAT_MS).note("About 12-15 nm of copper after the barrier.", "Thin copper lines.").detail("Grain and surface scattering raise resistivity.", &["COPPER LINE"]),
    Beat::new("LOW-K ILD between", BEAT_MS).note("SiOCH at k ~2.5-3; spacing is half the pitch; air gaps optional.", "The spaces between lines.").detail("Lower k, lower capacitance.", &["LOW-K ILD"]),
    Beat::new("the barrier's growing share", BEAT_MS).note("1-2 nm on three sides of every line, not scaling down.", "Close on one line.").detail("A bigger share each node.", &["BARRIER+LINER"]),
];
const TB_K: &[ChipKey] = &[
    ChipKey::at(THIN, 800.0, 0.35, 0.30, M2.spot(P::ThinMetal)).labels(&[(P::ThinMetal, "Cu core")]).title("copper line", "12-15 nm"),
    ChipKey::at(THIN, 760.0, 0.25, 0.20, M2).labels(&[(P::ThinMetal, "low-k between")]).title("low-k ILD", "k 2.5-3"),
    ChipKey::at(THIN, 700.0, 0.30, 0.25, M2.spot(P::ThinMetal)).labels(&[(P::ThinMetal, "barrier skin")]).title("barrier share", "doesn't scale"),
];
const TC_B: &[Beat] = &[
    Beat::new("DAMASCENE: cut the dielectric", BEAT_MS).note("Copper can't be dry-etched, so trenches are cut in the dielectric and filled.", "Copper inlaid in the level.").detail("Every copper node.", &["DAMASCENE"]),
    Beat::new("SUBTRACTIVE: etch the metal", BEAT_MS).note("Ru, Mo and W etch to volatile products, so lines can be etched from a blanket.", "The level lines standing alone.").detail("Allows air gaps, no liner.", &["SUBTRACTIVE"]),
    Beat::new("RUTHENIUM and MOLYBDENUM", BEAT_MS).note("Ru beats copper at 17 nm width and below in one analysis; imec etched Ru and Mo at 32 nm pitch and below.", "Thin lines carrying a signal.").detail("EM data still thin.", &["RUTHENIUM", "MOLYBDENUM"]),
];
const TC_K: &[ChipKey] = &[
    ChipKey::at(THIN, 1500.0, 0.40, 0.40, M2).title("damascene", "trench, fill, polish"),
    ChipKey::at(THIN, 1400.0, 0.45, 0.30, ChipState { explode: 0.4, ..M2 }).title("subtractive", "etch the metal"),
    ChipKey::at(THIN, 1500.0, 0.40, 0.40, ChipState { signal: 1.0, ..M2 }).title("Ru, Mo", "beyond copper"),
];
const TD_B: &[Beat] = &[
    Beat::new("a via by overlay alone", BEAT_MS).note("Placed by litho overlay, a via can miss its line.", "Vias between levels.").detail("Overlay needs ~1/4 of via pitch.", &["Overlay"]),
    Beat::new("misplaced: shorts and wall hits", BEAT_MS).note("A shifted via can short to a neighbour or hit the low-k wall.", "Close on a via.").detail("TDDB and yield risk.", &["EPE"]),
    Beat::new("SELF-ALIGNED VIA", BEAT_MS).note("The hole is bounded by the line below, so the via lands only on its own line.", "Vias landing cleanly.").detail("Selective dielectric growth.", &["SELF-ALIGNED VIA"]),
];
const TD_K: &[ChipKey] = &[
    ChipKey::at(THIN, 1500.0, 0.40, 0.35, M2.spot(P::Via)).labels(&[(P::Via, "via")]).title("overlay", "1/4 pitch budget"),
    ChipKey::at(THIN, 700.0, 0.30, 0.25, M2.spot(P::Via)).labels(&[(P::Via, "can miss")]).title("misplaced via", "short or wall hit"),
    ChipKey::at(THIN, 1400.0, 0.45, 0.35, ChipState { signal: 1.0, ..M2 }.spot(P::Via)).labels(&[(P::Via, "self-aligned")]).title("self-aligned via", "bounded by the line"),
];
const TE_B: &[Beat] = &[
    Beat::new("PIN ACCESS on M1/M2", BEAT_MS).note("Cell pins sit on M1/M2; the router must reach each one from above.", "Thin metal over a row of cells.").detail("Libraries require accessible tracks.", &["PIN ACCESS"]),
    Beat::new("fewer tracks, more congestion", BEAT_MS).note("7.5 to 6 to 5 tracks raises pin density; blockages can strand pins.", "More cells under the same metal.").detail("DTCO trades this.", &["Track height"]),
    Beat::new("routers solve it", BEAT_MS).note("Synopsys and Cadence place-and-route tools find paths; some M2 pins are hand-placed.", "Signals route along the thin metal.").detail("SNPS, CDNS.", &["EDA"]),
];
const TE_K: &[ChipKey] = &[
    ChipKey::at(THIN, 1700.0, 0.40, 0.45, M2).labels(&[(P::ThinMetal, "pins on M1/M2")]).title("pin access", "from above"),
    ChipKey::at(THIN, 1700.0, 0.40, 0.45, ChipState { cells: 5.0, ..M2 }).title("congestion", "fewer tracks"),
    ChipKey::at(THIN, 1500.0, 0.45, 0.40, ChipState { cells: 5.0, signal: 1.0, ..M2 }).title("routing", "place-and-route"),
];
const T_Z: [ZoomData; 5] = [
    ('a', "one damascene loop", TA_B, TA_K),
    ('b', "copper, low-k and the barrier", TB_B, TB_K),
    ('c', "damascene vs subtractive; Ru and Mo", TC_B, TC_K),
    ('d', "self-aligned vias", TD_B, TD_K),
    ('e', "pin access in standard cells", TE_B, TE_K),
];
const T7_B: &[Beat] = &[
    Beat::new("EUV 0.33 NA: ~26 nm pitch", BEAT_MS).note("Practical single-exposure limit about 26 nm pitch.", "Thin lines.").detail("13 nm half-pitch.", &["0.33 NA"]),
    Beat::new("High-NA 0.55: ~16 nm", BEAT_MS).note("About 16 nm pitch single exposure; Intel uses it on selected 18A layers.", "Tighter lines.").detail("Reported.", &["0.55 NA"]),
    Beat::new("TSMC N3E: 23 nm; imec Ru: 28 nm", BEAT_MS).note("N3E minimum metal pitch 23 nm; imec patterned 28 nm pitch Ru in one 0.33 NA exposure.", "Ruthenium lines.").detail("WikiChip, imec.", &["23 nm", "28 nm Ru"]),
];
const T7_K: &[ChipKey] = &[
    ChipKey::at(THIN, 1200.0, 0.40, 0.45, M2).title("EUV 0.33 NA", "~26 nm pitch"),
    ChipKey::at(THIN, 1400.0, 0.40, 0.45, M2).title("High-NA", "~16 nm pitch"),
    ChipKey::at(THIN, 1500.0, 0.45, 0.40, ChipState { signal: 1.0, ..M2 }).title("N3E 23 nm", "imec Ru 28 nm"),
];
const T8_B: &[Beat] = &[
    Beat::new("TSMC, Intel, Samsung set the rules", BEAT_MS).note("Pitch and metal choices.", "The thin stack.").detail("TSM, INTC.", &["Fabs"]),
    Beat::new("tool makers", BEAT_MS).note("Applied barrier/seed and Ru CVD; Lam and TEL etch and plate; ASML EUV.", "Levels forming.").detail("AMAT, LRCX, 8035.T, ASML.", &["Tools"]),
    Beat::new("designers and EDA", BEAT_MS).note("NVIDIA, AMD, Arm design cells that must route here; Synopsys and Cadence supply routers.", "Signals routing.").detail("NVDA, AMD, ARM, SNPS, CDNS.", &["Design"]),
];
const T8_K: &[ChipKey] = &[
    ChipKey::at(STACK, 2300.0, 0.45, 0.35, M6.spot(P::ThinMetal)).title("fabs", "TSMC, Intel, Samsung"),
    ChipKey::at(THIN, 1700.0, 0.45, 0.45, M2).title("tools", "Applied, Lam, TEL, ASML"),
    ChipKey::at(THIN, 1500.0, 0.45, 0.40, ChipState { cells: 5.0, signal: 1.0, ..M2 }).title("design, EDA", "routers"),
];
const T9_B: &[Beat] = &[
    Beat::new("Ru and Mo maturity", BEAT_MS).note("CMP, etch and cost for new metals aren't mature.", "Thin lines.").detail("Adoption risk.", &["Ru, Mo"]),
    Beat::new("RC beats gate delay", BEAT_MS).note("Thin-wire RC now dominates gate delay.", "Signals slowing along thin wire.").detail("Wires, not transistors, set speed.", &["RC"]),
    Beat::new("unpublished pitches", BEAT_MS).note("N2/14A metal pitches aren't public in the sources found; none are invented here.", "The stack.").detail("Notes.", &["Unknown"]),
];
const T9_K: &[ChipKey] = &[
    ChipKey::at(THIN, 1500.0, 0.40, 0.40, M2.spot(P::ThinMetal)).title("new metals", "maturity"),
    ChipKey::at(THIN, 1700.0, 0.45, 0.40, ChipState { signal: 1.0, ..M2 }).title("RC delay", "dominates"),
    ChipKey::at(STACK, 2300.0, 0.45, 0.35, M6).title("pitches", "not public"),
];
const T_S: [SecData; 9] = [(TA_B, TA_K), (TB_B, TB_K), (TC_B, TC_K), (TC_B, TC_K), (TD_B, TD_K), (TE_B, TE_K), (T7_B, T7_K), (T8_B, T8_K), (T9_B, T9_K)];
chip_node!(T_ZOOMS, T_SECTIONS, T_Z, T_S);
pub static THIN_NODE: ChipNode = ChipNode { page: "THIN METAL", beats: T_BEATS, keys: T_KEYS, zooms: &T_ZOOMS, zoom_data: &T_Z, sections: &T_SECTIONS, section_data: &T_S };

// ---------------------------------------------------------------- MID METAL

const M_BEATS: &[Beat] = &[
    Beat::new("the intermediate levels: M5-M9", OVERVIEW_MS)
        .note("Above the thin levels, M5-M9 route signals block to block: wider and taller lines.", "The stack, with the middle levels lit.").detail("Five dual-damascene passes.", &["M5-M9"]),
    Beat::new("dual damascene: via and trench in one fill", OVERVIEW_MS)
        .note("Each pass etches trench and via together and fills both with one copper plating and one CMP.", "A middle level with its vias.").detail("No barrier at the via bottom.", &["One fill, one CMP"]),
    Beat::new("RC delay: why levels get fatter", OVERVIEW_MS)
        .note("Delay ~ rho k eps0 L^2 / (W S): wider, taller lines cut R; spacing and low k cut C.", "Thin, medium and thick levels side by side in the stack.").detail("Cu resistivity rises below ~60 nm width.", &["~2.0 vs >3.0 uOhm-cm (IBM)"]),
    Beat::new("low-k between the lines, and it is soft", OVERVIEW_MS)
        .note("Lower-k dielectric cuts capacitance but is porous and soft: k 2.7 CDO is 7-10 GPa vs SiO2's 72.", "Close on the middle levels.").detail("Air gaps cut C by 25% or more.", &["LOW-K / ULK", "AIR GAP"]),
    Beat::new("current through the middle", OVERVIEW_MS)
        .note("Signals climb through the vias into the middle levels and across the chip.", "Pulses climb the stack.").detail("EM: atoms drift along the cap interface.", &["Black: MTTF ~ J^-n exp(Ea/kT)"]),
    Beat::new("electromigration: the wear-out", OVERVIEW_MS)
        .note("High current density pushes copper atoms, opening voids; caps and liners slow it.", "A hot middle level.").detail("Cu Ea ~0.7-1.1 eV vs Al 0.5-0.7.", &["ELECTROMIGRATION"]),
    Beat::new("the whole stack, exploded", OVERVIEW_MS)
        .note("Pulled apart: thin, medium and thick levels, each with its vias.", "The stack separates.").detail("Applied FY2025: 30% of revenue from China.", &["$8,529M of $28,368M"]),
];
const M_KEYS: &[ChipKey] = &[
    ChipKey::at(STACK, 2300.0, 0.45, 0.35, M6.spot(P::MidMetal)).labels(&[(P::MidMetal, "M5-M9")]).notes(P::MidMetal, Some(P::ThinMetal)),
    ChipKey::at(MID, 1100.0, 0.40, 0.40, M4.spot(P::MidMetal).spot(P::Via)).labels(&[(P::MidMetal, "trench"), (P::Via, "via, same fill")]).notes(P::Via, Some(P::MidMetal)),
    ChipKey::at(STACK, 2000.0, 0.35, 0.10, M6).labels(&[(P::ThinMetal, "thin: high R"), (P::MidMetal, "medium"), (P::TopMetal, "thick: low R")]).notes(P::MidMetal, Some(P::TopMetal)),
    ChipKey::at(MID, 800.0, 0.30, 0.25, M4.spot(P::MidMetal)).labels(&[(P::MidMetal, "low-k between")]).notes(P::MidMetal, None),
    ChipKey::at(STACK, 2200.0, 0.45, 0.30, SIG).labels(&[(P::MidMetal, "signals across")]).notes(P::MidMetal, Some(P::Via)),
    ChipKey::at(MID, 1000.0, 0.40, 0.35, ChipState { heat: 0.8, signal: 1.0, ..M4 }.spot(P::MidMetal)).labels(&[(P::MidMetal, "EM risk")]).notes(P::MidMetal, None),
    ChipKey::at([0.0, 450.0, 0.0], 2700.0, 0.45, 0.30, EXP.spot(P::MidMetal)).labels(&[(P::MidMetal, "medium levels")]).notes(P::MidMetal, Some(P::Via)),
];
const MA_B: &[Beat] = &[
    Beat::new("DEPOSIT ILD and PATTERN+ETCH", BEAT_MS).note("Low-k stack with etch stop; trench and via cut through a hard mask.", "The level about to form.").detail("Each pass 4-6 tool visits.", &["DEPOSIT ILD", "PATTERN+ETCH"]),
    Beat::new("BARRIER+SEED and PLATE Cu", BEAT_MS).note("TaN/Ta, Ru seed; copper plated bottom-up into trench and via together.", "Copper fills the level.").detail("ECD tools.", &["BARRIER+SEED", "PLATE Cu"]),
    Beat::new("CMP and CAP+REPEAT", BEAT_MS).note("Polish off excess, cap with SiCN/SiN, do the next level.", "The next level stacks on.").detail("Five passes for M5-M9.", &["CMP", "CAP+REPEAT"]),
];
const MA_K: &[ChipKey] = &[
    ChipKey::at(MID, 1100.0, 0.40, 0.40, ChipState { metal: 2.0, ..DEVS }).title("deposit, pattern, etch", "trench + via"),
    ChipKey::at(MID, 1100.0, 0.45, 0.40, ChipState { metal: 3.0, ..DEVS }.spot(P::MidMetal)).labels(&[(P::MidMetal, "plated Cu")]).title("barrier, seed, plate", "one fill"),
    ChipKey::at(MID, 1100.0, 0.50, 0.40, M4.spot(P::MidMetal)).title("CMP, cap, repeat", "next level"),
];
const MB_B: &[Beat] = &[
    Beat::new("R falls with width and height", BEAT_MS).note("R = rho L / (W H).", "Thin and thick levels.").detail("Thick levels: lowest R.", &["R"]),
    Beat::new("C grows with k and H/S", BEAT_MS).note("C is mostly line to line.", "Close on neighbouring lines.").detail("Low k and spacing help.", &["C"]),
    Beat::new("RC DELAY ~ L^2", BEAT_MS).note("Delay grows with length squared: long wires belong on fat levels.", "A signal crossing the stack.").detail("rho k eps0 L^2 / (W S).", &["RC DELAY"]),
];
const MB_K: &[ChipKey] = &[
    ChipKey::at(STACK, 2000.0, 0.35, 0.10, M6).labels(&[(P::ThinMetal, "thin"), (P::TopMetal, "thick")]).title("resistance", "rho L / (W H)"),
    ChipKey::at(MID, 800.0, 0.30, 0.25, M4.spot(P::MidMetal)).title("capacitance", "k, H/S"),
    ChipKey::at(STACK, 2200.0, 0.45, 0.30, SIG).title("RC delay", "~ L^2"),
];
const MC_B: &[Beat] = &[
    Beat::new("LOW-K / ULK: lower k, softer film", BEAT_MS).note("SiO2 72 GPa; k 2.7 CDO 7-10 GPa; porous 3 GPa.", "The middle levels.").detail("Modulus falls 10x as k drops a third.", &["LOW-K / ULK"]),
    Beat::new("AIR GAP: no dielectric at all", BEAT_MS).note("Removing the dielectric between lines cuts capacitance 25% or more.", "Lines with gaps between.").detail("Intel: -25% with subtractive Ru.", &["AIR GAP"]),
    Beat::new("RU / SUBTRACTIVE", BEAT_MS).note("Below ~20 nm pitch, etched Ru without a barrier replaces damascene copper.", "Lines etched apart.").detail("Intel IEDM 2024: <=25 nm.", &["RU / SUBTRACTIVE"]),
];
const MC_K: &[ChipKey] = &[
    ChipKey::at(MID, 800.0, 0.30, 0.25, M4.spot(P::MidMetal)).title("low-k", "soft and porous"),
    ChipKey::at(MID, 900.0, 0.35, 0.25, ChipState { explode: 0.3, ..M4 }).title("air gap", "-25% C"),
    ChipKey::at(THIN, 1400.0, 0.45, 0.30, ChipState { explode: 0.4, ..M2 }).title("Ru subtractive", "<=25 nm pitch"),
];
const MD_B: &[Beat] = &[
    Beat::new("current pushes atoms", BEAT_MS).note("Electrons drag copper atoms along the copper/cap interface.", "A level carrying current.").detail("Voids upstream, hillocks downstream.", &["ELECTROMIGRATION"]),
    Beat::new("Black's equation", BEAT_MS).note("MTTF = A J^-n exp(Ea/kT), n ~2; hotter and denser is shorter-lived.", "The level heats.").detail("Cu Ea 0.7-1.1 eV.", &["MTTF"]),
    Beat::new("caps and liners", BEAT_MS).note("CoWP, Co or Ru caps and Mn or Co liners slow the drift.", "The level cools.").detail("Cu reflow too.", &["Fixes"]),
];
const MD_K: &[ChipKey] = &[
    ChipKey::at(MID, 1000.0, 0.40, 0.35, ChipState { signal: 1.0, ..M4 }.spot(P::MidMetal)).title("electromigration", "atoms drift"),
    ChipKey::at(MID, 1000.0, 0.40, 0.35, ChipState { heat: 1.0, signal: 1.0, ..M4 }.spot(P::MidMetal)).title("Black's equation", "J^-n exp(Ea/kT)"),
    ChipKey::at(MID, 1000.0, 0.45, 0.35, ChipState { signal: 1.0, ..M4 }).title("caps, liners", "slow the drift"),
];
const ME_B: &[Beat] = &[
    Beat::new("VIA / EPE: a clean landing", BEAT_MS).note("A via landed on target has low resistance.", "Vias between middle levels.").detail("Overlay ~1/4 pitch at <=70 nm.", &["VIA / EPE"]),
    Beat::new("misaligned: narrow bottom", BEAT_MS).note("A shifted via narrows at the bottom: R up, short or EM risk.", "Close on a via.").detail("Edge placement error.", &["EPE"]),
    Beat::new("EDA RC EXTRACT", BEAT_MS).note("StarRC and Quantus extract every wire's R and C for timing signoff.", "Signals across the stack.").detail("SNPS, CDNS.", &["EDA RC EXTRACT"]),
];
const ME_K: &[ChipKey] = &[
    ChipKey::at(MID, 1000.0, 0.40, 0.35, M4.spot(P::Via)).labels(&[(P::Via, "via")]).title("via landing", "low R"),
    ChipKey::at(MID, 700.0, 0.30, 0.25, M4.spot(P::Via)).labels(&[(P::Via, "misaligned")]).title("EPE", "R up, risk up"),
    ChipKey::at(STACK, 2200.0, 0.45, 0.30, SIG).title("RC extraction", "StarRC, Quantus"),
];
const M_Z: [ZoomData; 5] = [
    ('a', "one dual-damascene pass", MA_B, MA_K),
    ('b', "RC delay", MB_B, MB_K),
    ('c', "low-k, air gaps and ruthenium", MC_B, MC_K),
    ('d', "electromigration", MD_B, MD_K),
    ('e', "vias, edge placement and RC extraction", ME_B, ME_K),
];
const M4_B: &[Beat] = &[
    Beat::new("Intel 7 and Intel 4", BEAT_MS).note("Intel 7 M2/M4 44/52 nm (DUV multi); Intel 4 M2/M4 45 nm with some EUV; Intel 4 M0 30 nm SAQP.", "The middle levels.").detail("EUV VS MULTI per level.", &["Intel"]),
    Beat::new("TSMC N5 and N3E", BEAT_MS).note("N5 Mx ~30% tighter than N7 with EUV; N3E M0 23 nm EUV single pattern.", "Tighter lines.").detail("N3B used EUV double on 3 layers.", &["TSMC"]),
    Beat::new("no full tables", BEAT_MS).note("Foundries don't publish per-level pitches; M5-M9 is a class label.", "The stack.").detail("Disclosed examples only.", &["Notes"]),
];
const M4_K: &[ChipKey] = &[
    ChipKey::at(MID, 1100.0, 0.40, 0.40, M4.spot(P::MidMetal)).title("Intel 7, Intel 4", "44-52 nm, EUV"),
    ChipKey::at(THIN, 1500.0, 0.40, 0.40, M2).title("TSMC N5, N3E", "23 nm M0"),
    ChipKey::at(STACK, 2300.0, 0.45, 0.35, M6).title("no full tables", "class labels"),
];
const M8_B: &[Beat] = &[
    Beat::new("tool makers", BEAT_MS).note("Applied (Endura CuBS, Black Diamond), Lam (SABRE plating), TEL, Ebara.", "Middle levels forming.").detail("AMAT, LRCX, 8035.T, 6361.T.", &["Tools"]),
    Beat::new("fabs and designers", BEAT_MS).note("TSMC, Intel, Samsung build it; Arm, NVIDIA, AMD design to its rules.", "The stack.").detail("TSM, INTC, 005930.KS.", &["Fabs"]),
    Beat::new("Applied and China", BEAT_MS).note("China was 30% ($8,529M) of Applied's $28,368M FY2025 revenue.", "Signals across the stack.").detail("Export-control exposure.", &["30% China"]),
];
const M8_K: &[ChipKey] = &[
    ChipKey::at(MID, 1100.0, 0.45, 0.40, M4.spot(P::MidMetal)).title("tools", "Applied, Lam, TEL, Ebara"),
    ChipKey::at(STACK, 2300.0, 0.45, 0.35, M6).title("fabs, designers", "TSMC, Intel, Samsung"),
    ChipKey::at(STACK, 2200.0, 0.45, 0.30, SIG).title("Applied: 30% China", "FY2025"),
];
const M9_B: &[Beat] = &[
    Beat::new("copper's resistance wall", BEAT_MS).note("Below ~20 nm pitch copper loses to Ru.", "Thin lines.").detail("Size effect.", &["Cu wall"]),
    Beat::new("ULK damage and EM", BEAT_MS).note("Porous low-k damages easily; higher current speeds electromigration.", "A hot middle level.").detail("Reliability.", &["ULK, EM"]),
    Beat::new("tool and China shifts", BEAT_MS).note("Subtractive Ru changes who sells the tools; China is 30% of Applied's sales.", "The stack.").detail("Market risk.", &["Shifts"]),
];
const M9_K: &[ChipKey] = &[
    ChipKey::at(THIN, 1400.0, 0.45, 0.30, M2.spot(P::ThinMetal)).title("Cu wall", "<20 nm pitch"),
    ChipKey::at(MID, 1000.0, 0.40, 0.35, ChipState { heat: 1.0, signal: 1.0, ..M4 }).title("ULK, EM", "reliability"),
    ChipKey::at(STACK, 2300.0, 0.45, 0.35, M6).title("market shifts", "Ru tools, China"),
];
const M_S: [SecData; 9] = [(MA_B, MA_K), (MA_B, MA_K), (MB_B, MB_K), (M4_B, M4_K), (MC_B, MC_K), (MD_B, MD_K), (ME_B, ME_K), (M8_B, M8_K), (M9_B, M9_K)];
chip_node!(M_ZOOMS, M_SECTIONS, M_Z, M_S);
pub static MID_NODE: ChipNode = ChipNode { page: "MID METAL", beats: M_BEATS, keys: M_KEYS, zooms: &M_ZOOMS, zoom_data: &M_Z, sections: &M_SECTIONS, section_data: &M_S };

// ---------------------------------------------------------------- TOP METAL

const BSP: ChipState = ChipState { backside: 1.0, arch: 2.0, ..M6 };
const P_BEATS: &[Beat] = &[
    Beat::new("the thick top: M10-M14", OVERVIEW_MS)
        .note("The top levels are the thickest and widest copper: power grid, clock trunk and long wires.", "The stack with the top levels lit.").detail("Same damascene loop, bigger.", &["M10-M14"]),
    Beat::new("the power grid", OVERVIEW_MS)
        .note("Vdd and Vss stripes on the thick levels feed current down to every cell.", "Close on the thick top levels.").detail("R = rho L / (W T): thick and wide cuts R.", &["POWER GRID"]),
    Beat::new("current flows down the stack", OVERVIEW_MS)
        .note("Supply current runs from the bumps down through M14 to M1 and the cell rails.", "Pulses run down through the vias.").detail("Every stage drops V = I x R.", &["IR DROP"]),
    Beat::new("IR drop and heat", OVERVIEW_MS)
        .note("Resistance along the path drops the voltage the transistors see; current density heats the metal.", "The top levels glow hot.").detail("~10% total droop tolerated (secondary).", &["EM LIMIT: Cu ~1-3e6 A/cm2"]),
    Beat::new("pads, passivation, bumps", OVERVIEW_MS)
        .note("Above the top metal: bond pads, SiN and polyimide passivation, then C4 bumps at ~150 um pitch.", "The top of the stack.").detail("Microbumps ~40 um; hybrid bonds <=10 um.", &["C4 ~150 um", "Microbump ~40 um"]),
    Beat::new("backside power: rails moved underneath", OVERVIEW_MS)
        .note("Backside power puts the power network under the thinned silicon, reached by nano-TSVs; the front carries signals only.", "Copper rails appear under the transistors.").detail("PowerVia test chip: >30% lower droop.", &["BSPDN"]),
    Beat::new("the whole stack, exploded", OVERVIEW_MS)
        .note("Transistors at the bottom, thin, medium and thick levels above, power below with backside delivery.", "The stack separates.").detail("TSMC A16: volume Q4 2026.", &["Intel 18A, TSMC A16"]),
];
const P_KEYS: &[ChipKey] = &[
    ChipKey::at(STACK, 2300.0, 0.45, 0.35, M6.spot(P::TopMetal)).labels(&[(P::TopMetal, "M10-M14")]).notes(P::TopMetal, Some(P::MidMetal)),
    ChipKey::at(TOP, 1200.0, 0.40, 0.45, M6.spot(P::TopMetal)).labels(&[(P::TopMetal, "power grid")]).notes(P::TopMetal, None),
    ChipKey::at(STACK, 2200.0, 0.45, 0.30, SIG).labels(&[(P::TopMetal, "current in"), (P::Contact, "down to the cells")]).notes(P::TopMetal, Some(P::Contact)),
    ChipKey::at(TOP, 1300.0, 0.40, 0.40, ChipState { heat: 1.0, ..SIG }).labels(&[(P::TopMetal, "hot, dropping V")]).notes(P::TopMetal, None),
    ChipKey::at(TOP, 1100.0, 0.30, 0.60, M6.spot(P::TopMetal)).labels(&[(P::TopMetal, "pads and bumps above")]).notes(P::TopMetal, None),
    ChipKey::at([0.0, 50.0, 0.0], 1600.0, 0.40, -0.05, BSP).labels(&[(P::TopMetal, "backside rails"), (P::Via, "nano-TSV")]).notes(P::TopMetal, Some(P::Via)),
    ChipKey::at([0.0, 400.0, 0.0], 2800.0, 0.45, 0.25, ChipState { explode: 1.0, ..BSP }).labels(&[(P::TopMetal, "thick levels")]).notes(P::TopMetal, Some(P::ThinMetal)),
];
const PA_B: &[Beat] = &[
    Beat::new("TRENCH ETCH, BARRIER + SEED", BEAT_MS).note("Dual damascene trenches; TaN and copper PVD seed.", "The thick level forming.").detail("Wider and taller.", &["TRENCH ETCH"]),
    Beat::new("CU PLATE, CMP", BEAT_MS).note("Copper fill, polish flat.", "Thick copper fills in.").detail("Same loop as thin levels.", &["CU PLATE", "CMP"]),
    Beat::new("PAD + PASSIV, BUMP", BEAT_MS).note("Bond pads, SiN + polyimide, then under-bump metal and solder.", "The top of the stack.").detail("Ready for the package.", &["PAD + PASSIV", "BUMP"]),
];
const PA_K: &[ChipKey] = &[
    ChipKey::at(TOP, 1200.0, 0.40, 0.45, ChipState { metal: 4.5, ..DEVS }).title("trench, barrier, seed", "thick level"),
    ChipKey::at(TOP, 1200.0, 0.45, 0.45, M6.spot(P::TopMetal)).labels(&[(P::TopMetal, "thick Cu")]).title("plate, CMP", "same loop, bigger"),
    ChipKey::at(TOP, 1100.0, 0.30, 0.60, M6.spot(P::TopMetal)).title("pads, passivation, bumps", "to the package"),
];
const PB_B: &[Beat] = &[
    Beat::new("POWER GRID", BEAT_MS).note("Vdd/Vss stripes feeding every cell.", "The thick grid.").detail("Wide, low R.", &["POWER GRID"]),
    Beat::new("CLOCK TRUNK and LONG WIRES", BEAT_MS).note("The clock's low-skew spine and buses crossing blocks.", "Signals along the top levels.").detail("Reach needs low R.", &["CLOCK TRUNK", "LONG WIRES"]),
    Beat::new("RDL and UNDERFILL", BEAT_MS).note("A redistribution layer re-routes pads to bumps; underfill epoxy spreads stress.", "The top of the stack.").detail("Package side.", &["RDL", "UNDERFILL"]),
];
const PB_K: &[ChipKey] = &[
    ChipKey::at(TOP, 1200.0, 0.40, 0.45, M6.spot(P::TopMetal)).labels(&[(P::TopMetal, "Vdd / Vss")]).title("power grid", "feeds every cell"),
    ChipKey::at(TOP, 1300.0, 0.45, 0.40, SIG.spot(P::TopMetal)).labels(&[(P::TopMetal, "clock, buses")]).title("clock and long wires", "low R, long reach"),
    ChipKey::at(TOP, 1100.0, 0.30, 0.60, M6.spot(P::TopMetal)).title("RDL, underfill", "package side"),
];
const PC_B: &[Beat] = &[
    Beat::new("from the VRM to the transistor", BEAT_MS).note("Board regulator, package planes, bumps, M14 down to M1, cell rail, transistor.", "Current runs down the stack.").detail("0.9 V illustrative.", &["Path"]),
    Beat::new("IR DROP at every stage", BEAT_MS).note("V = I x R drops voltage at each stage; the die sees what's left.", "The top glows.").detail("~10% tolerated (secondary).", &["IR DROP"]),
    Beat::new("EM LIMIT", BEAT_MS).note("Copper carries ~1-3e6 A/cm2 before electromigration bites, ~5x aluminium.", "Hot metal.").detail("Wider wires, redundant vias.", &["EM LIMIT"]),
];
const PC_K: &[ChipKey] = &[
    ChipKey::at(STACK, 2200.0, 0.45, 0.30, SIG).title("power path", "VRM to transistor"),
    ChipKey::at(TOP, 1300.0, 0.40, 0.40, ChipState { heat: 0.7, ..SIG }).title("IR drop", "V = I x R"),
    ChipKey::at(TOP, 1200.0, 0.40, 0.40, ChipState { heat: 1.0, ..SIG }).title("EM limit", "~1-3e6 A/cm2"),
];
const PD_B: &[Beat] = &[
    Beat::new("C4 BUMP: ~150 um", BEAT_MS).note("Solder balls from chip to package substrate.", "The top of the stack.").detail("Patent example.", &["C4 BUMP"]),
    Beat::new("MICROBUMP: ~40 um", BEAT_MS).note("Solder-capped copper pillars from chiplet to interposer; a wall near 10 um.", "Close on the top.").detail("20-25 um bump + 15 um space.", &["MICROBUMP"]),
    Beat::new("HYBRID BOND: <=10 um", BEAT_MS).note("Direct copper-to-copper and oxide-to-oxide, no solder, die to die.", "The top level close up.").detail("More connections per mm2.", &["HYBRID BOND"]),
];
const PD_K: &[ChipKey] = &[
    ChipKey::at(TOP, 1200.0, 0.30, 0.60, M6.spot(P::TopMetal)).title("C4 bumps", "~150 um pitch"),
    ChipKey::at(TOP, 900.0, 0.30, 0.55, M6.spot(P::TopMetal)).title("microbumps", "~40 um pitch"),
    ChipKey::at(TOP, 700.0, 0.30, 0.50, M6.spot(P::TopMetal)).title("hybrid bonds", "<=10 um pitch"),
];
const PE_B: &[Beat] = &[
    Beat::new("front-side power: shared stack", BEAT_MS).note("Today power and signals share M0-M14.", "The front stack.").detail("Congestion and droop.", &["Frontside"]),
    Beat::new("BSPDN: power from behind", BEAT_MS).note("Backside metals (BM0-BM5) under thinned silicon, nano-TSVs up to the devices.", "Rails under the transistors.").detail("Intel PowerVia, TSMC A16.", &["BSPDN"]),
    Beat::new("the gains", BEAT_MS).note("PowerVia test chip: >30% lower droop, >6% speed; M0 relaxed 30 to 36 nm. A16 vs N2P: +8-10% speed.", "Signals on the front, power behind.").detail("18A brief: ~10x lower worst-case droop.", &["Claims"]),
];
const PE_K: &[ChipKey] = &[
    ChipKey::at(STACK, 2300.0, 0.45, 0.35, SIG).title("frontside power", "shared stack"),
    ChipKey::at([0.0, 50.0, 0.0], 1600.0, 0.40, -0.05, BSP).labels(&[(P::TopMetal, "backside rails")]).title("backside power", "BM0-BM5, nano-TSV"),
    ChipKey::at([0.0, 300.0, 0.0], 2400.0, 0.45, 0.20, ChipState { signal: 1.0, ..BSP }).title("gains", ">30% lower droop"),
];
const P_Z: [ZoomData; 5] = [
    ('a', "the top loop: metal, pads, bumps", PA_B, PA_K),
    ('b', "jobs of the thick levels", PB_B, PB_K),
    ('c', "power delivery and IR drop", PC_B, PC_K),
    ('d', "bumps to hybrid bonds", PD_B, PD_K),
    ('e', "backside power (BSPDN)", PE_B, PE_K),
];
const P2_B: &[Beat] = &[
    Beat::new("transistors and thin metal", BEAT_MS).note("Transistors, contacts, M1-M4.", "The bottom of the stack.").detail("Cell wiring.", &["Bottom"]),
    Beat::new("medium metal", BEAT_MS).note("M5-M9, block signals.", "The middle.").detail("Wider.", &["Middle"]),
    Beat::new("thick metal and bumps", BEAT_MS).note("M10-M14, pads, passivation, C4 bumps.", "The top.").detail("Fattest wires.", &["Top"]),
];
const P2_K: &[ChipKey] = &[
    ChipKey::at(THIN, 1400.0, 0.45, 0.35, M6.spot(P::ThinMetal)).title("thin", "M1-M4"),
    ChipKey::at(MID, 1400.0, 0.45, 0.35, M6.spot(P::MidMetal)).title("medium", "M5-M9"),
    ChipKey::at(TOP, 1400.0, 0.45, 0.40, M6.spot(P::TopMetal)).title("thick", "M10-M14"),
];
const P7_B: &[Beat] = &[
    Beat::new("pitches: C4 to hybrid", BEAT_MS).note("C4 ~150 um, microbump 40 um, hybrid <=10 um.", "The top.").detail("Patents, SemiEngineering.", &["Pitches"]),
    Beat::new("Intel stacks", BEAT_MS).note("Intel 4: M0 30 nm, 16 metal layers; 18A: M0-M14 front + BM0-BM5 back.", "The stack, exploded.").detail("WikiChip, SemiAnalysis.", &["Intel"]),
    Beat::new("money", BEAT_MS).note("Intel 2025 $52.9B; Synopsys FY2025 $7.1B; Cadence $5.3B; TSMC ~US$122B.", "A powered stack.").detail("Different scales.", &["Revenue"]),
];
const P7_K: &[ChipKey] = &[
    ChipKey::at(TOP, 1100.0, 0.30, 0.60, M6.spot(P::TopMetal)).title("pitches", "150 / 40 / 10 um"),
    ChipKey::at([0.0, 400.0, 0.0], 2800.0, 0.45, 0.25, ChipState { explode: 1.0, ..BSP }).title("Intel stacks", "16 layers; BM0-BM5"),
    ChipKey::at(STACK, 2300.0, 0.45, 0.35, SIG).title("revenue", "Intel, SNPS, CDNS, TSMC"),
];
const P8_B: &[Beat] = &[
    Beat::new("TSMC and Intel", BEAT_MS).note("TSMC: A16 backside power late 2026. Intel: PowerVia on 18A in Panther Lake.", "Backside rails.").detail("TSM, INTC.", &["Fabs"]),
    Beat::new("NVIDIA, AMD, Arm", BEAT_MS).note("Huge supply currents and microbump 2.5D/3D parts; Arm IP must fit the grid.", "A powered stack.").detail("NVDA, AMD, ARM.", &["Designers"]),
    Beat::new("Synopsys, Cadence", BEAT_MS).note("IR-drop, EM and power-network sign-off tools.", "The hot top.").detail("SNPS, CDNS.", &["EDA"]),
];
const P8_K: &[ChipKey] = &[
    ChipKey::at([0.0, 50.0, 0.0], 1600.0, 0.40, -0.05, BSP).title("TSMC, Intel", "backside power"),
    ChipKey::at(STACK, 2300.0, 0.45, 0.35, SIG).title("NVIDIA, AMD, Arm", "big currents"),
    ChipKey::at(TOP, 1300.0, 0.40, 0.40, ChipState { heat: 0.8, ..SIG }).title("Synopsys, Cadence", "sign-off"),
];
const P9_B: &[Beat] = &[
    Beat::new("IR drop and electromigration", BEAT_MS).note("Droop from grid to rail; EM in thin wires, vias and bumps.", "Hot top metal.").detail("Wider grid, redundant vias.", &["Droop, EM"]),
    Beat::new("voids and bridging", BEAT_MS).note("Via/barrier voids in damascene; bump bridging at fine pitch.", "Close on the top.").detail("Process control, Cu pillars.", &["Voids"]),
    Beat::new("thermal-cycle fatigue", BEAT_MS).note("C4 joints crack from die/substrate expansion mismatch; underfill gives >10x life.", "The top with its bumps.").detail("Top pitches are confidential.", &["Fatigue"]),
];
const P9_K: &[ChipKey] = &[
    ChipKey::at(TOP, 1300.0, 0.40, 0.40, ChipState { heat: 1.0, ..SIG }).title("droop, EM", "grid to rail"),
    ChipKey::at(TOP, 800.0, 0.30, 0.45, M6.spot(P::Via)).title("voids, bridging", "fine pitch"),
    ChipKey::at(TOP, 1100.0, 0.30, 0.60, M6.spot(P::TopMetal)).title("fatigue", "underfill: >10x life"),
];
const P_S: [SecData; 9] = [(PA_B, PA_K), (P2_B, P2_K), (PB_B, PB_K), (PC_B, PC_K), (PD_B, PD_K), (PE_B, PE_K), (P7_B, P7_K), (P8_B, P8_K), (P9_B, P9_K)];
chip_node!(P_ZOOMS, P_SECTIONS, P_Z, P_S);
pub static TOP_NODE: ChipNode = ChipNode { page: "TOP METAL", beats: P_BEATS, keys: P_KEYS, zooms: &P_ZOOMS, zoom_data: &P_Z, sections: &P_SECTIONS, section_data: &P_S };
