// Packaging tab pages (LOGIC DIE, MICROBUMP, INTERPOSER, SUBSTRATE, ASSEMBLY, BOARD):
// one 3D package in poly3d (`render_pkg`), on the Memory tab's template. Each node is
// its overview beats, five zooms and nine sections, all keyframes over the same rig.
// Sources: section 10 of each PKG_*.txt page.

use super::diagrams_scene_pkg::{pkg_node, PkgNode, PkgState, SecData, ZoomData, BASE, BEAT_MS, DIES, LOW, OVERVIEW_MS, P, PKG};
use crate::ui::anim::Beat;
use poly3d::PkgKey;

// ---- shared states ----------------------------------------------------------------

const FULL: PkgState = PkgState { data: 1.0, power: 0.5, ..BASE };
const BARE: PkgState = PkgState { stacks: 0.0, interposer: 0.0, substrate: 0.0, board: 0.0, bga: 0.0, ..BASE };
const DIE_ONLY: PkgState = PkgState { stacks: 0.0, ..BARE };
const EXP: PkgState = PkgState { explode: 1.0, ubump: 1.0, c4: 1.0, ..BASE };
const CUT: PkgState = PkgState { cut: 1.0, ubump: 1.0, c4: 1.0, ..BASE };
const CHIPLET: PkgState = PkgState { split: 1.0, bridges: 1.0, stacks: 8.0, isize: 1.25, ..FULL };
const HOT: PkgState = PkgState { heat: 1.0, power: 1.0, data: 0.6, ..BASE };
const COOLED: PkgState = PkgState { lid: 1.0, cooler: 1.0, heat: 0.6, power: 0.8, ..BASE };
const FAR: f64 = 2300.0;

macro_rules! k {
    ($t:expr, $d:expr, $y:expr, $p:expr, $s:expr) => {
        PkgKey::at($t, $d, $y, $p, $s)
    };
}

// =================================================================== LOGIC DIE

const L_B: &[Beat] = &[
    Beat::new("the logic die: the GPU itself", OVERVIEW_MS).note("The compute die sits at the centre of the package, built on a leading-edge node.", "One large purple die, alone.").detail("Everything else in the package serves it.", &["N4/N3-class nodes"]),
    Beat::new("as big as one exposure allows", OVERVIEW_MS).note("A scanner prints one 26 x 33 mm field; the die can't be larger. H100 is about 814 mm2, ~95% of it.", "A pink outline marks the reticle field over the die.").detail("High-NA halves the field in one direction.", &["Reticle 26 x 33 mm = 858 mm2", "H100 ~814 mm2"]),
    Beat::new("big dies yield worse", OVERVIEW_MS).note("A random defect scraps the whole die; at ~800 mm2, estimates put yield near half.", "The die glows under test.").detail("Smaller dies waste less per defect.", &["~45-47% at 800-814 mm2 (estimates)"]),
    Beat::new("HBM along its edges", OVERVIEW_MS).note("HBM stacks connect along the die's edges, so the edge length limits how many fit.", "Four HBM stacks appear beside the die on an interposer.").detail("More memory needs more shoreline.", &["HBM SHORELINE"]),
    Beat::new("chiplets: two dies, one GPU", OVERVIEW_MS).note("Past the reticle, the design splits into two dies joined by a ~10 TB/s link, with eight stacks.", "The die splits in two; more stacks line the sides.").detail("Blackwell: two dies on CoWoS-L.", &["Die-to-die ~10 TB/s", "Memory ~8 TB/s"]),
    Beat::new("data and power at once", OVERVIEW_MS).note("Memory traffic runs through the interposer while power climbs from the board.", "Cyan data and yellow power flow.").detail("The die is where it all meets.", &["Thousands of bumps"]),
    Beat::new("and heat to remove", OVERVIEW_MS).note("The die turns its power into heat that must leave through the top.", "The die glows hot; heat rises.").detail("See BOARD for cooling.", &["HEAT"]),
];
const L_K: &[PkgKey] = &[
    k!(DIES, 1200.0, 0.45, 0.55, DIE_ONLY).labels(&[(P::Logic, "logic die")]).notes(P::Logic, None),
    k!(DIES, 1200.0, 0.30, 0.95, PkgState { reticle: 1.0, ..DIE_ONLY }).labels(&[(P::Reticle, "26 x 33 mm field")]).notes(P::Reticle, Some(P::Logic)),
    k!(DIES, 1150.0, 0.50, 0.60, PkgState { heat: 0.4, ..DIE_ONLY }).labels(&[(P::Logic, "one defect = one die")]).notes(P::Logic, None),
    k!(PKG, 1800.0, 0.45, 0.70, PkgState { substrate: 0.0, board: 0.0, bga: 0.0, ..BASE }).labels(&[(P::Hbm, "HBM on the edges")]).notes(P::Hbm, Some(P::Logic)),
    k!(PKG, 2100.0, 0.40, 0.75, PkgState { substrate: 0.0, board: 0.0, bga: 0.0, ..CHIPLET }).labels(&[(P::Logic, "two dies"), (P::Bridge, "bridge")]).notes(P::Logic, Some(P::Bridge)),
    k!(PKG, FAR, 0.45, 0.45, FULL).labels(&[(P::Interposer, "data"), (P::Substrate, "power")]).notes(P::Logic, Some(P::Interposer)),
    k!(PKG, FAR, 0.40, 0.40, HOT).labels(&[(P::Logic, "heat")]).notes(P::Logic, None),
];
const LA_B: &[Beat] = &[
    Beat::new("one field: 26 x 33 mm", BEAT_MS).note("The scanner's field is the hard cap on die size.", "The reticle outline.").detail("858 mm2.", &["RETICLE LIMIT"]),
    Beat::new("H100: ~814 mm2", BEAT_MS).note("Big AI dies fill ~95% of it.", "The die fills the outline.").detail("Secondary sources.", &["DIE SIZE"]),
    Beat::new("no room left", BEAT_MS).note("More silicon now means more dies, not a bigger one.", "The die splits.").detail("CHIPLETS.", &["Next: chiplets"]),
];
const LA_K: &[PkgKey] = &[
    k!(DIES, 1200.0, 0.30, 0.95, PkgState { reticle: 1.0, die: 0.7, ..DIE_ONLY }).title("reticle field", "26 x 33 mm"),
    k!(DIES, 1200.0, 0.30, 0.95, PkgState { reticle: 1.0, ..DIE_ONLY }).title("H100", "~814 mm2"),
    k!(DIES, 1300.0, 0.35, 0.90, PkgState { reticle: 1.0, split: 1.0, ..DIE_ONLY }).title("past the limit", "chiplets"),
];
const LB_B: &[Beat] = &[
    Beat::new("a defect on a big die", BEAT_MS).note("One defect scraps all ~800 mm2.", "One big die.").detail("Yield ~45-47% (estimates).", &["YIELD"]),
    Beat::new("the same defect on a chiplet", BEAT_MS).note("Split in two, one defect scraps only half the silicon.", "Two dies.").detail("More good silicon per wafer.", &["Chiplets"]),
    Beat::new("KNOWN GOOD DIE", BEAT_MS).note("Each die is tested before packaging, so only good ones are assembled.", "The dies glow under test.").detail("Protects the HBM.", &["KGD"]),
];
const LB_K: &[PkgKey] = &[
    k!(DIES, 1150.0, 0.50, 0.60, PkgState { heat: 0.5, ..DIE_ONLY }).title("big die", "one defect, all scrap"),
    k!(DIES, 1250.0, 0.45, 0.60, PkgState { split: 1.0, ..DIE_ONLY }).title("chiplets", "half the loss"),
    k!(DIES, 1250.0, 0.40, 0.60, PkgState { split: 1.0, power: 0.8, ..DIE_ONLY }).title("known good die", "test before packaging"),
];
const LC_B: &[Beat] = &[
    Beat::new("two dies side by side", BEAT_MS).note("Blackwell uses two compute dies.", "Two dies on an interposer.").detail("One GPU to software.", &["CHIPLETS"]),
    Beat::new("a bridge under the seam", BEAT_MS).note("A silicon bridge under the joint carries the fine wires.", "The bridge lights.").detail("CoWoS-L.", &["LSI bridge"]),
    Beat::new("~10 TB/s between them", BEAT_MS).note("The die-to-die link runs at about 10 TB/s.", "Green data crosses the seam.").detail("Tom's Hardware.", &["DIE-TO-DIE ~10 TB/s"]),
];
const LC_K: &[PkgKey] = &[
    k!(PKG, 1700.0, 0.40, 0.75, PkgState { substrate: 0.0, board: 0.0, bga: 0.0, split: 1.0, bridges: 1.0, ..BASE }).title("two dies", "Blackwell"),
    k!(DIES, 1000.0, 0.30, 0.30, PkgState { substrate: 0.0, board: 0.0, bga: 0.0, split: 1.0, bridges: 1.0, explode: 0.6, cut: 0.5, ..BASE }.spot(P::Bridge)).labels(&[(P::Bridge, "silicon bridge")]).title("bridge", "under the seam"),
    k!(DIES, 1300.0, 0.40, 0.60, PkgState { substrate: 0.0, board: 0.0, bga: 0.0, split: 1.0, bridges: 1.0, data: 1.0, ..BASE }).title("die-to-die", "~10 TB/s"),
];
const LD_B: &[Beat] = &[
    Beat::new("four stacks on the edges", BEAT_MS).note("Each HBM stack needs a stretch of die edge.", "Four stacks.").detail("SHORELINE.", &["4 stacks"]),
    Beat::new("eight stacks need more edge", BEAT_MS).note("More stacks need more edge, so the die grows or splits.", "Eight stacks around two dies.").detail("Blackwell.", &["8 stacks"]),
    Beat::new("data along every edge", BEAT_MS).note("Each stack feeds the die through the interposer.", "Data flows from every stack.").detail("~8 TB/s memory bandwidth.", &["~8 TB/s"]),
];
const LD_K: &[PkgKey] = &[
    k!(PKG, 1800.0, 0.40, 0.85, PkgState { substrate: 0.0, board: 0.0, bga: 0.0, ..BASE }).title("4 stacks", "on the edges"),
    k!(PKG, 2100.0, 0.40, 0.85, PkgState { substrate: 0.0, board: 0.0, bga: 0.0, ..CHIPLET }).title("8 stacks", "more edge"),
    k!(PKG, 2100.0, 0.40, 0.70, PkgState { substrate: 0.0, board: 0.0, bga: 0.0, ..CHIPLET }).title("data", "~8 TB/s"),
];
const LE_B: &[Beat] = &[
    Beat::new("power in", BEAT_MS).note("Hundreds of amps climb into the die.", "Yellow power rises.").detail("Through thousands of bumps.", &["Power"]),
    Beat::new("heat out", BEAT_MS).note("All of it leaves as heat through the top.", "The die glows.").detail("HEAT.", &["Heat"]),
    Beat::new("a lid and a cold plate", BEAT_MS).note("A lid spreads the heat into a cold plate.", "Lid and cold plate on top.").detail("See BOARD.", &["Cooling"]),
];
const LE_K: &[PkgKey] = &[
    k!(PKG, FAR, 0.40, 0.35, PkgState { power: 1.0, ..BASE }).title("power in", "hundreds of amps"),
    k!(PKG, FAR, 0.40, 0.35, HOT).title("heat out", "through the top"),
    k!(PKG, 2500.0, 0.40, 0.30, COOLED).title("cooling", "lid, cold plate"),
];
const L_Z: [ZoomData; 5] = [('a', "the reticle limit", LA_B, LA_K), ('b', "yield and known-good dies", LB_B, LB_K), ('c', "chiplets and the die-to-die link", LC_B, LC_K), ('d', "HBM shoreline", LD_B, LD_K), ('e', "power and heat", LE_B, LE_K)];
const L_S: [SecData; 9] = [(LA_B, LA_K), (LD_B, LD_K), (LB_B, LB_K), (LA_B, LA_K), (LB_B, LB_K), (LC_B, LC_K), (LE_B, LE_K), (LC_B, LC_K), (LB_B, LB_K)];
pkg_node!(L_ZOOMS, L_SECTIONS, L_Z, L_S);
pub static LOGIC: PkgNode = PkgNode { page: "LOGIC DIE", beats: L_B, keys: L_K, zooms: &L_ZOOMS, zoom_data: &L_Z, sections: &L_SECTIONS, section_data: &L_S };

// =================================================================== MICROBUMP

const U_B: &[Beat] = &[
    Beat::new("a finished package", OVERVIEW_MS).note("From outside, the package is a stack of dies on an interposer on a substrate.", "The package on its board.").detail("Bumps join every level.", &["3 levels of joints"]),
    Beat::new("pulled apart: bumps at every level", OVERVIEW_MS).note("Separated, each level shows its bumps: C4 under the interposer, microbumps under the dies.", "The levels lift apart, bumps showing.").detail("Plus BGA balls below.", &["C4 ~150 um", "Microbump ~40 um"]),
    Beat::new("microbumps under the dies", OVERVIEW_MS).note("A dense grid of copper pillars with solder caps joins each die to the interposer at ~40 um pitch.", "Close on the dense bump grid under the dies.").detail("20-25 um bumps, 15 um spacing.", &["MICROBUMP ~40 um"]),
    Beat::new("C4 bumps under the interposer", OVERVIEW_MS).note("Coarser solder balls at ~150 um join the interposer to the substrate.", "The coarser bumps below the interposer.").detail("Patent example.", &["C4 ~150 um"]),
    Beat::new("power climbs through the bumps", OVERVIEW_MS).note("Every amp for the die passes through these joints.", "Yellow power climbs level by level.").detail("Shrinking bumps raise current density.", &["ELECTROMIGRATION"]),
    Beat::new("underfill shares the stress", OVERVIEW_MS).note("Epoxy flows between the levels so stress spreads across the area.", "Dark underfill fills the gaps.").detail(">10x thermal-cycle life for C4.", &["UNDERFILL"]),
    Beat::new("hybrid bonds: no bumps at all", OVERVIEW_MS).note("Below ~10 um pitch, copper bonds directly to copper and the gap disappears.", "The bumps vanish and the dies sit flat on the interposer.").detail("TSMC SoIC.", &["HYBRID BOND <=10 um"]),
];
const U_K: &[PkgKey] = &[
    k!(PKG, FAR, 0.45, 0.45, BASE).labels(&[(P::Logic, "dies"), (P::Substrate, "substrate")]).notes(P::Interposer, None),
    k!(PKG, 2500.0, 0.40, 0.25, EXP).labels(&[(P::Ubump, "microbumps"), (P::C4, "C4 bumps")]).notes(P::Ubump, Some(P::C4)),
    k!(DIES, 900.0, 0.35, 0.15, PkgState { explode: 0.7, ..EXP }.spot(P::Ubump)).labels(&[(P::Ubump, "~40 um pitch")]).notes(P::Ubump, None),
    k!(LOW, 1100.0, 0.35, 0.10, PkgState { explode: 0.7, ..EXP }.spot(P::C4)).labels(&[(P::C4, "~150 um pitch")]).notes(P::C4, None),
    k!(PKG, 2300.0, 0.40, 0.20, PkgState { power: 1.0, ..EXP }).labels(&[(P::C4, "current through bumps")]).notes(P::C4, Some(P::Logic)),
    k!(PKG, 1800.0, 0.40, 0.15, PkgState { underfill: 1.0, ubump: 1.0, c4: 1.0, cut: 1.0, ..BASE }).labels(&[(P::Underfill, "underfill")]).notes(P::Underfill, None),
    k!(DIES, 1000.0, 0.35, 0.15, PkgState { hybrid: 1.0, cut: 1.0, ubump: 1.0, ..BASE }).labels(&[(P::Logic, "bonded flat")]).notes(P::Logic, None),
];
const UA_B: &[Beat] = &[
    Beat::new("C4 BUMP: ~150 um", BEAT_MS).note("Solder balls to the substrate.", "The C4 row.").detail("Coarsest.", &["C4"]),
    Beat::new("MICROBUMP: ~40 um", BEAT_MS).note("Copper pillars under the dies.", "The dense microbump grid.").detail("~16x the density of C4.", &["Microbump"]),
    Beat::new("HYBRID BOND: <=10 um", BEAT_MS).note("Direct copper-to-copper.", "Dies flat on the interposer.").detail("No solder.", &["Hybrid"]),
];
const UA_K: &[PkgKey] = &[
    k!(LOW, 1100.0, 0.35, 0.10, PkgState { explode: 0.7, ..EXP }.spot(P::C4)).title("C4", "~150 um"),
    k!(DIES, 900.0, 0.35, 0.15, PkgState { explode: 0.7, ..EXP }.spot(P::Ubump)).title("microbump", "~40 um"),
    k!(DIES, 1000.0, 0.35, 0.15, PkgState { hybrid: 1.0, cut: 1.0, ubump: 1.0, ..BASE }).title("hybrid bond", "<=10 um"),
];
const UB_B: &[Beat] = &[
    Beat::new("copper pillars plated", BEAT_MS).note("Pillars plated on the die, solder caps on top.", "The die lifted above its bumps.").detail("CU PILLAR.", &["Plating"]),
    Beat::new("placed and reflowed", BEAT_MS).note("Face down on the interposer, heated until the solder joins.", "The die settles onto its bumps.").detail("REFLOW.", &["Reflow"]),
    Beat::new("underfilled", BEAT_MS).note("Epoxy wicks under and cures.", "Underfill fills the gap.").detail("UNDERFILL.", &["Underfill"]),
];
const UB_K: &[PkgKey] = &[
    k!(DIES, 1100.0, 0.40, 0.20, PkgState { explode: 1.0, ..EXP }).title("pillars", "plated, capped"),
    k!(DIES, 1100.0, 0.40, 0.20, PkgState { explode: 0.0, ..EXP }).title("reflow", "solder joins"),
    k!(DIES, 1100.0, 0.40, 0.15, PkgState { underfill: 1.0, ..EXP }).title("underfill", "cured epoxy"),
];
const UC_B: &[Beat] = &[
    Beat::new("halve the pitch, 4x the joints", BEAT_MS).note("Density goes with one over pitch squared.", "Dense microbumps.").detail("BUMP PITCH.", &["1 / pitch^2"]),
    Beat::new("solder bridges near 10 um", BEAT_MS).note("Below ~10 um, molten solder can bridge neighbours.", "Close on the bumps.").detail("Microbumps hit a wall.", &["~10 um wall"]),
    Beat::new("hybrid bonding past the wall", BEAT_MS).note("Copper-to-copper bonds need near-perfect flatness but go to a few um.", "Dies bonded flat.").detail("TSMC SoIC.", &["SoIC"]),
];
const UC_K: &[PkgKey] = &[
    k!(DIES, 900.0, 0.35, 0.15, PkgState { explode: 0.7, ..EXP }.spot(P::Ubump)).title("bump pitch", "density ~ 1/p^2"),
    k!(DIES, 700.0, 0.30, 0.10, PkgState { explode: 0.4, ..EXP }.spot(P::Ubump)).title("solder wall", "~10 um"),
    k!(DIES, 1000.0, 0.35, 0.15, PkgState { hybrid: 1.0, cut: 1.0, ubump: 1.0, ..BASE }).title("hybrid bonding", "SoIC"),
];
const UD_B: &[Beat] = &[
    Beat::new("different expansion rates", BEAT_MS).note("Die, interposer and substrate expand differently when hot.", "The package heating.").detail("Stress concentrates in the outer joints.", &["CTE mismatch"]),
    Beat::new("the substrate warps", BEAT_MS).note("The big organic substrate bows.", "The substrate bends.").detail("Bumps take the strain.", &["WARPAGE"]),
    Beat::new("underfill spreads the load", BEAT_MS).note("Epoxy shares the stress over the whole area: >10x C4 life.", "Underfill between levels.").detail("UCLA (Totta).", &["UNDERFILL"]),
];
const UD_K: &[PkgKey] = &[
    k!(PKG, 2000.0, 0.40, 0.15, PkgState { heat: 0.8, cut: 1.0, ubump: 1.0, c4: 1.0, ..BASE }).title("expansion", "die vs substrate"),
    k!(PKG, 2000.0, 0.40, 0.10, PkgState { warp: 1.0, cut: 1.0, ubump: 1.0, c4: 1.0, ..BASE }).title("warpage", "the substrate bows"),
    k!(PKG, 2000.0, 0.40, 0.15, PkgState { underfill: 1.0, cut: 1.0, ubump: 1.0, c4: 1.0, ..BASE }).title("underfill", ">10x life"),
];
const UE_B: &[Beat] = &[
    Beat::new("thousands of bumps carry power", BEAT_MS).note("Power for the die enters through thousands of joints.", "Power climbs through the bumps.").detail("Each shares the current.", &["Power bumps"]),
    Beat::new("smaller bumps, more current each", BEAT_MS).note("Shrinking raises current density per joint.", "Hot bumps.").detail("ELECTROMIGRATION.", &["Current density"]),
    Beat::new("more bumps share the load", BEAT_MS).note("Finer pitch also means more bumps to share current.", "A dense grid carrying power.").detail("A design trade.", &["Trade"]),
];
const UE_K: &[PkgKey] = &[
    k!(PKG, 2300.0, 0.40, 0.20, PkgState { power: 1.0, ..EXP }).title("power bumps", "thousands"),
    k!(DIES, 1000.0, 0.35, 0.15, PkgState { power: 1.0, heat: 0.6, explode: 0.7, ..EXP }).title("current density", "electromigration"),
    k!(DIES, 1000.0, 0.40, 0.15, PkgState { power: 1.0, explode: 0.7, ..EXP }.spot(P::Ubump)).title("share the load", "more bumps"),
];
const U_Z: [ZoomData; 5] = [('a', "C4, microbump, hybrid bond", UA_B, UA_K), ('b', "making a joint", UB_B, UB_K), ('c', "pitch and the solder wall", UC_B, UC_K), ('d', "stress, warpage and underfill", UD_B, UD_K), ('e', "current through the bumps", UE_B, UE_K)];
const U_S: [SecData; 9] = [(UA_B, UA_K), (UA_B, UA_K), (UB_B, UB_K), (UC_B, UC_K), (UC_B, UC_K), (UD_B, UD_K), (UE_B, UE_K), (UB_B, UB_K), (UC_B, UC_K)];
pkg_node!(U_ZOOMS, U_SECTIONS, U_Z, U_S);
pub static UBUMP: PkgNode = PkgNode { page: "MICROBUMP", beats: U_B, keys: U_K, zooms: &U_ZOOMS, zoom_data: &U_Z, sections: &U_SECTIONS, section_data: &U_S };

// =================================================================== INTERPOSER

const IP: PkgState = PkgState { substrate: 0.0, board: 0.0, bga: 0.0, ..BASE };
const I_B: &[Beat] = &[
    Beat::new("the interposer: wiring under the dies", OVERVIEW_MS).note("A slab of fine wiring carries thousands of connections between the GPU and its HBM.", "The interposer under the logic die and four stacks.").detail("TSMC calls the package CoWoS.", &["CoWoS"]),
    Beat::new("data runs across it", OVERVIEW_MS).note("Each stack's 1024-bit bus crosses the interposer to the GPU.", "Cyan data flows from each stack, through the interposer, into the die.").detail("Silicon wiring is fine enough.", &["1024 bits per HBM3 stack"]),
    Beat::new("power runs down through TSVs", OVERVIEW_MS).note("TSVs carry power and signals down to the C4 bumps and substrate.", "Cut open: the interposer between bump rows, power climbing.").detail("Every amp passes through.", &["TSV"]),
    Beat::new("CoWoS-S: one silicon slab, up to ~3.3x reticle", OVERVIEW_MS).note("A full silicon interposer handles up to about 3.3x reticle size, ~2,700 mm2.", "The full package with a silicon interposer.").detail("TSMC's page.", &["COWOS-S ~3.3x reticle"]),
    Beat::new("CoWoS-L: silicon bridges in an organic interposer", OVERVIEW_MS).note("Beyond that, small silicon bridges sit only under the joints, inside an organic interposer.", "Two dies, eight stacks, cyan bridges under the seams.").detail("Blackwell uses CoWoS-L.", &["COWOS-L", "~10 TB/s die-to-die"]),
    Beat::new("growing past the reticle", OVERVIEW_MS).note("TSMC plans 9.5-reticle interposers with 12 HBM stacks in 2027 and over 14 reticles with 24 by 2029.", "The interposer grows.").detail("Tom's Hardware.", &["9.5x (2027)", ">14x (2029)"]),
    Beat::new("capacity is the bottleneck", OVERVIEW_MS).note("Almost every high-end AI accelerator uses CoWoS; its capacity has limited shipments.", "The whole package on its board.").detail("Bigger interposers, fewer per wafer.", &["CoWoS capacity"]),
];
const I_K: &[PkgKey] = &[
    k!(PKG, 1700.0, 0.45, 0.55, IP.spot(P::Interposer)).labels(&[(P::Interposer, "interposer")]).notes(P::Interposer, Some(P::Hbm)),
    k!(PKG, 1700.0, 0.40, 0.65, PkgState { data: 1.0, ..IP }).labels(&[(P::Hbm, "HBM"), (P::Logic, "GPU")]).notes(P::Interposer, Some(P::Logic)),
    k!(DIES, 1300.0, 0.35, 0.10, PkgState { power: 1.0, ..CUT }).labels(&[(P::Interposer, "TSVs")]).notes(P::Interposer, Some(P::C4)),
    k!(PKG, FAR, 0.45, 0.45, FULL).labels(&[(P::Interposer, "silicon, CoWoS-S")]).notes(P::Interposer, None),
    k!(PKG, 2300.0, 0.40, 0.70, PkgState { substrate: 0.0, board: 0.0, bga: 0.0, ..CHIPLET }).labels(&[(P::Bridge, "LSI bridge"), (P::Interposer, "organic")]).notes(P::Bridge, Some(P::Interposer)),
    k!(PKG, 2700.0, 0.40, 0.70, PkgState { isize: 1.5, ..CHIPLET }).labels(&[(P::Interposer, "bigger every year")]).notes(P::Interposer, None),
    k!(PKG, 2700.0, 0.45, 0.40, PkgState { isize: 1.5, ..CHIPLET }).labels(&[(P::Interposer, "CoWoS")]).notes(P::Interposer, None),
];
const IA_B: &[Beat] = &[
    Beat::new("COWOS-S: full silicon", BEAT_MS).note("One slab, fine wiring, TSVs.", "A silicon interposer.").detail("Up to ~3.3x reticle.", &["COWOS-S"]),
    Beat::new("COWOS-R: polymer RDL", BEAT_MS).note("Copper in polymer: cheaper, coarser.", "An RDL interposer.").detail("RDL.", &["COWOS-R"]),
    Beat::new("COWOS-L: bridges where needed", BEAT_MS).note("Silicon bridges in an organic interposer.", "Bridges under the seams.").detail("Blackwell.", &["COWOS-L"]),
];
const IA_K: &[PkgKey] = &[
    k!(PKG, 1700.0, 0.45, 0.60, IP.spot(P::Interposer)).title("CoWoS-S", "silicon"),
    k!(PKG, 1700.0, 0.45, 0.60, PkgState { bridges: 0.6, ..IP }.spot(P::Interposer)).title("CoWoS-R", "RDL"),
    k!(PKG, 2100.0, 0.40, 0.70, PkgState { substrate: 0.0, board: 0.0, bga: 0.0, ..CHIPLET }.spot(P::Bridge)).title("CoWoS-L", "LSI bridges"),
];
const IB_B: &[Beat] = &[
    Beat::new("out of the HBM base die", BEAT_MS).note("Data leaves the stack through microbumps.", "Data from a stack.").detail("1024 bits.", &["Out"]),
    Beat::new("across the fine wiring", BEAT_MS).note("It crosses millimetres of silicon wiring.", "Data across the interposer.").detail("WIRING DENSITY.", &["Across"]),
    Beat::new("up into the GPU", BEAT_MS).note("And rises into the logic die.", "Data into the die.").detail("Thousands in parallel.", &["In"]),
];
const IB_K: &[PkgKey] = &[
    k!(DIES, 1100.0, 0.45, 0.40, PkgState { data: 1.0, ..IP }.spot(P::Hbm)).title("from HBM", "microbumps"),
    k!(DIES, 1100.0, 0.40, 0.40, PkgState { data: 1.0, ..IP }.spot(P::Interposer)).title("across", "fine wiring"),
    k!(DIES, 1100.0, 0.35, 0.40, PkgState { data: 1.0, ..IP }.spot(P::Logic)).title("into the GPU", "1024 bits per stack"),
];
const IC_B: &[Beat] = &[
    Beat::new("3.3x reticle today", BEAT_MS).note("CoWoS-S up to ~2,700 mm2.", "A four-stack package.").detail("TSMC.", &["3.3x"]),
    Beat::new("9.5x in 2027", BEAT_MS).note("12 HBM stacks.", "A bigger interposer, eight stacks.").detail("Roadmap.", &["9.5x"]),
    Beat::new(">14x by 2029", BEAT_MS).note("Up to 24 HBM5E stacks.", "Bigger still.").detail("Tom's Hardware.", &[">14x"]),
];
const IC_K: &[PkgKey] = &[
    k!(PKG, 1900.0, 0.40, 0.70, IP).title("3.3x reticle", "today"),
    k!(PKG, 2500.0, 0.40, 0.70, PkgState { substrate: 0.0, board: 0.0, bga: 0.0, isize: 1.3, ..CHIPLET }).title("9.5x reticle", "2027 plan"),
    k!(PKG, 3000.0, 0.40, 0.70, PkgState { substrate: 0.0, board: 0.0, bga: 0.0, isize: 1.7, ..CHIPLET }).title(">14x reticle", "2029 plan"),
];
const ID_B: &[Beat] = &[
    Beat::new("TSV: through the interposer", BEAT_MS).note("Copper columns carry power and signals down.", "Cut open, bumps above and below.").detail("TSV.", &["TSV"]),
    Beat::new("power climbs up", BEAT_MS).note("Every amp comes up through the TSV array.", "Power climbing.").detail("Many TSVs share it.", &["Power"]),
    Beat::new("to the C4 bumps below", BEAT_MS).note("The TSVs land on the C4 bumps to the substrate.", "The C4 row.").detail("~150 um pitch.", &["C4"]),
];
const ID_K: &[PkgKey] = &[
    k!(DIES, 1200.0, 0.35, 0.10, CUT.spot(P::Interposer)).title("TSVs", "through the interposer"),
    k!(DIES, 1200.0, 0.35, 0.10, PkgState { power: 1.0, ..CUT }).title("power", "up through TSVs"),
    k!(LOW, 1100.0, 0.35, 0.10, CUT.spot(P::C4)).title("C4", "to the substrate"),
];
const IE_B: &[Beat] = &[
    Beat::new("bigger interposers, fewer per wafer", BEAT_MS).note("Interposers are cut from wafers; larger ones mean fewer per wafer.", "A big interposer.").detail("Tom's Hardware.", &["Packages per wafer"]),
    Beat::new("one supplier does most", BEAT_MS).note("TSMC does most CoWoS; UMC supplies interposers, ASE and Amkor assemble.", "The package.").detail("TrendForce.", &["TSMC"]),
    Beat::new("capacity limits AI output", BEAT_MS).note("CoWoS capacity, not wafers, has capped high-end accelerator shipments.", "A finished package.").detail("Reports.", &["Capacity"]),
];
const IE_K: &[PkgKey] = &[
    k!(PKG, 2700.0, 0.40, 0.70, PkgState { isize: 1.5, ..CHIPLET }).title("wafer area", "fewer per wafer"),
    k!(PKG, FAR, 0.45, 0.45, FULL).title("suppliers", "TSMC, UMC, ASE, Amkor"),
    k!(PKG, 2700.0, 0.45, 0.40, PkgState { isize: 1.5, lid: 1.0, ..CHIPLET }).title("capacity", "the bottleneck"),
];
const I_Z: [ZoomData; 5] = [('a', "CoWoS-S, -R and -L", IA_B, IA_K), ('b', "a signal from HBM to GPU", IB_B, IB_K), ('c', "growing past the reticle", IC_B, IC_K), ('d', "TSVs and power", ID_B, ID_K), ('e', "capacity", IE_B, IE_K)];
const I_S: [SecData; 9] = [(IA_B, IA_K), (IA_B, IA_K), (IB_B, IB_K), (IA_B, IA_K), (IA_B, IA_K), (IC_B, IC_K), (IB_B, IB_K), (IE_B, IE_K), (IE_B, IE_K)];
pkg_node!(I_ZOOMS, I_SECTIONS, I_Z, I_S);
pub static INTERPOSER: PkgNode = PkgNode { page: "INTERPOSER", beats: I_B, keys: I_K, zooms: &I_ZOOMS, zoom_data: &I_Z, sections: &I_SECTIONS, section_data: &I_S };

// =================================================================== SUBSTRATE

const SB: PkgState = PkgState { cut: 1.0, c4: 1.0, ..BASE };
const S_B: &[Beat] = &[
    Beat::new("the substrate under the interposer", OVERVIEW_MS).note("A laminate of copper and insulating film fans the interposer's bumps out to the board.", "The brown substrate under the interposer.").detail("12-20 layers for AI GPUs (estimates).", &["Organic substrate"]),
    Beat::new("C4 bumps on top", OVERVIEW_MS).note("The interposer lands on it through C4 bumps at ~150 um.", "Cut open: the C4 row between interposer and substrate.").detail("Patent example.", &["C4 ~150 um"]),
    Beat::new("build-up layers of ABF and copper", OVERVIEW_MS).note("Layer after layer of ABF film and copper wiring, laminated onto a core.", "Copper layers show in the substrate's cut face.").detail("Ajinomoto ~95% of ABF (estimate).", &["ABF FILM", "BUILD-UP LAYERS"]),
    Beat::new("BGA balls below", OVERVIEW_MS).note("Its underside carries BGA balls at ~1 mm that solder to the board.", "Low view: the ball grid under the substrate.").detail("FAN-OUT from 150 um to ~1 mm.", &["BGA"]),
    Beat::new("power fans in from the board", OVERVIEW_MS).note("Power and high-speed signals route through the layers.", "Power climbs from the board through the substrate.").detail("Power planes.", &["Fan-out"]),
    Beat::new("warpage: the big laminate bends", OVERVIEW_MS).note("A large, thin organic laminate bows as it heats and cools.", "The substrate bends.").detail("Glass cores could be flatter.", &["WARPAGE", "GLASS CORE"]),
    Beat::new("bigger packages, bigger substrates", OVERVIEW_MS).note("Multi-die layouts roughly double substrate area per package; few makers yield 14+ layers.", "A large two-die package.").detail("Ibiden, Shinko, Unimicron, AT&S, Nan Ya.", &["SUBSTRATE MAKERS"]),
];
const S_K: &[PkgKey] = &[
    k!(PKG, FAR, 0.45, 0.35, BASE.spot(P::Substrate)).labels(&[(P::Substrate, "substrate")]).notes(P::Substrate, Some(P::Interposer)),
    k!(LOW, 1300.0, 0.35, 0.10, SB.spot(P::C4)).labels(&[(P::C4, "C4")]).notes(P::C4, Some(P::Substrate)),
    k!(LOW, 1200.0, 0.30, 0.10, PkgState { layers: 1.0, ..SB }.spot(P::Substrate)).labels(&[(P::Substrate, "ABF + Cu layers")]).notes(P::Substrate, None),
    k!(LOW, 1500.0, 0.40, -0.10, PkgState { explode: 0.6, ..SB }.spot(P::Bga)).labels(&[(P::Bga, "BGA balls")]).notes(P::Bga, Some(P::Board)),
    k!(PKG, FAR, 0.40, 0.25, PkgState { power: 1.0, ..BASE }).labels(&[(P::Substrate, "power planes")]).notes(P::Substrate, Some(P::Board)),
    k!(LOW, 1800.0, 0.40, 0.08, PkgState { warp: 1.0, ..SB }).labels(&[(P::Substrate, "warpage")]).notes(P::Substrate, None),
    k!(PKG, 2700.0, 0.40, 0.40, PkgState { isize: 1.4, ..CHIPLET }.spot(P::Substrate)).labels(&[(P::Substrate, "twice the area")]).notes(P::Substrate, None),
];
const SA_B: &[Beat] = &[
    Beat::new("a CORE", BEAT_MS).note("Start from a stiff core with plated through-holes.", "The substrate.").detail("Fights warpage.", &["CORE"]),
    Beat::new("ABF FILM laminated", BEAT_MS).note("A layer of insulating film goes on.", "Layers start to show.").detail("Ajinomoto.", &["ABF"]),
    Beat::new("BUILD-UP LAYERS, one by one", BEAT_MS).note("Drill, plate, laminate, repeat: 12-20 layers.", "All layers in the cut face.").detail("Estimates.", &["12-20 layers"]),
];
const SA_K: &[PkgKey] = &[
    k!(LOW, 1200.0, 0.30, 0.10, PkgState { layers: 0.15, ..SB }.spot(P::Substrate)).title("core", "plated through-holes"),
    k!(LOW, 1200.0, 0.30, 0.10, PkgState { layers: 0.5, ..SB }.spot(P::Substrate)).title("ABF film", "insulating layer"),
    k!(LOW, 1200.0, 0.30, 0.10, PkgState { layers: 1.0, ..SB }.spot(P::Substrate)).title("build-up", "12-20 layers"),
];
const SB_B: &[Beat] = &[
    Beat::new("150 um bumps on top", BEAT_MS).note("C4 bumps from the interposer.", "The C4 row.").detail("Fine pitch.", &["C4"]),
    Beat::new("routed through the layers", BEAT_MS).note("Wires spread out layer by layer.", "The layers.").detail("FAN-OUT.", &["Fan-out"]),
    Beat::new("~1 mm balls below", BEAT_MS).note("BGA balls at board pitch.", "The ball grid.").detail("BGA.", &["BGA"]),
];
const SB_K: &[PkgKey] = &[
    k!(LOW, 1300.0, 0.35, 0.10, SB.spot(P::C4)).title("C4", "~150 um"),
    k!(LOW, 1200.0, 0.30, 0.10, PkgState { layers: 1.0, ..SB }).title("fan-out", "through the layers"),
    k!(LOW, 1500.0, 0.40, -0.10, PkgState { explode: 0.6, ..SB }.spot(P::Bga)).title("BGA", "~1 mm"),
];
const SC_B: &[Beat] = &[
    Beat::new("flat when cool", BEAT_MS).note("At room temperature the substrate is flat.", "A flat substrate.").detail("Mostly.", &["Flat"]),
    Beat::new("bowed when hot", BEAT_MS).note("During reflow it bows, stressing every joint.", "The substrate bends.").detail("WARPAGE.", &["Warp"]),
    Beat::new("GLASS CORE: stiffer, flatter", BEAT_MS).note("Glass cores, under development, could stay flatter.", "A flatter substrate.").detail("Not yet in volume.", &["Glass"]),
];
const SC_K: &[PkgKey] = &[
    k!(LOW, 1800.0, 0.40, 0.08, SB).title("flat", "cool"),
    k!(LOW, 1800.0, 0.40, 0.08, PkgState { warp: 1.0, heat: 0.6, ..SB }).title("warpage", "hot"),
    k!(LOW, 1800.0, 0.40, 0.08, PkgState { warp: 0.2, ..SB }.spot(P::Substrate)).title("glass core", "flatter"),
];
const SD_B: &[Beat] = &[
    Beat::new("Ajinomoto: the film", BEAT_MS).note("~95% of CPU/GPU-grade ABF (analyst estimate).", "The layers.").detail("Single supplier.", &["ABF FILM"]),
    Beat::new("SUBSTRATE MAKERS", BEAT_MS).note("Ibiden, Shinko, Unimicron, AT&S, Nan Ya; shares are estimates that disagree.", "The substrate.").detail("Ibiden ~JPY 500B for two fabs.", &["Makers"]),
    Beat::new("14+ layers are hard", BEAT_MS).note("Few makers yield GPU-class 14+ layer substrates at volume (estimate).", "A big substrate.").detail("Capacity risk.", &["Layers"]),
];
const SD_K: &[PkgKey] = &[
    k!(LOW, 1200.0, 0.30, 0.10, PkgState { layers: 1.0, ..SB }.spot(P::Substrate)).title("ABF film", "Ajinomoto ~95%"),
    k!(PKG, FAR, 0.45, 0.35, BASE.spot(P::Substrate)).title("substrate makers", "Ibiden, Shinko, Unimicron"),
    k!(PKG, 2700.0, 0.40, 0.40, PkgState { isize: 1.4, ..CHIPLET }.spot(P::Substrate)).title("14+ layers", "hard to yield"),
];
const SE_B: &[Beat] = &[
    Beat::new("power planes", BEAT_MS).note("Wide copper planes carry hundreds of amps up from the board.", "Power climbs.").detail("Low resistance.", &["Power"]),
    Beat::new("high-speed signals", BEAT_MS).note("Signal layers carry the GPU's links out.", "The layers.").detail("Shielded by planes.", &["Signals"]),
    Beat::new("all through one laminate", BEAT_MS).note("Every connection to the outside world crosses the substrate.", "The whole package.").detail("FAN-OUT.", &["One path"]),
];
const SE_K: &[PkgKey] = &[
    k!(PKG, FAR, 0.40, 0.25, PkgState { power: 1.0, ..BASE }).title("power planes", "hundreds of amps"),
    k!(LOW, 1200.0, 0.30, 0.10, PkgState { layers: 1.0, data: 1.0, ..SB }).title("signals", "shielded layers"),
    k!(PKG, FAR, 0.45, 0.35, FULL).title("one laminate", "everything crosses it"),
];
const S_Z: [ZoomData; 5] = [('a', "building the layers", SA_B, SA_K), ('b', "fan-out: C4 to BGA", SB_B, SB_K), ('c', "warpage and glass cores", SC_B, SC_K), ('d', "ABF film and substrate makers", SD_B, SD_K), ('e', "power planes and signals", SE_B, SE_K)];
const S_S: [SecData; 9] = [(SB_B, SB_K), (SA_B, SA_K), (SA_B, SA_K), (SD_B, SD_K), (SD_B, SD_K), (SC_B, SC_K), (SB_B, SB_K), (SD_B, SD_K), (SC_B, SC_K)];
pkg_node!(S_ZOOMS, S_SECTIONS, S_Z, S_S);
pub static SUBSTRATE: PkgNode = PkgNode { page: "SUBSTRATE", beats: S_B, keys: S_K, zooms: &S_ZOOMS, zoom_data: &S_Z, sections: &S_SECTIONS, section_data: &S_S };

// =================================================================== ASSEMBLY

const WAFER: PkgState = PkgState { substrate: 0.0, board: 0.0, bga: 0.0, count: 3.0, stacks: 0.0, ..BASE };
const A_B: &[Beat] = &[
    Beat::new("known-good dies arrive", OVERVIEW_MS).note("Tested logic dies and HBM stacks wait to be assembled.", "Bare dies.").detail("Only known-good ones.", &["KNOWN GOOD DIE"]),
    Beat::new("CHIP ON WAFER: onto the interposer wafer", OVERVIEW_MS).note("Dies are bonded face down onto a whole, uncut interposer wafer.", "Several interposers in a row with dies landing.").detail("Then underfill and thinning to reveal TSVs.", &["CoW"]),
    Beat::new("HBM stacks join", OVERVIEW_MS).note("The HBM stacks are bonded beside each logic die.", "Stacks appear on every interposer.").detail("Microbumps and reflow.", &["REFLOW"]),
    Beat::new("cut apart, then ON SUBSTRATE", OVERVIEW_MS).note("The wafer is cut into interposers, each bonded onto a substrate by C4 reflow.", "One interposer settles onto a substrate.").detail("CoWoS.", &["oS"]),
    Beat::new("UNDERFILL FLOW", OVERVIEW_MS).note("Epoxy wicks under each level and cures.", "Underfill fills the gaps.").detail(">10x joint life.", &["Underfill"]),
    Beat::new("lid and TEST", OVERVIEW_MS).note("A lid goes on and the package is tested; a late defect scraps everything, HBM included.", "The lidded package under test.").detail("YIELD STACKUP: 10 parts at 99% = ~90%.", &["Test"]),
    Beat::new("CAPACITY: the bottleneck", OVERVIEW_MS).note("CoWoS capacity has limited AI accelerator shipments; NVIDIA reportedly took 40-50% in 2024.", "Finished packages in a row.").detail("ASE and Amkor add capacity (OSAT).", &["Capacity"]),
];
const A_K: &[PkgKey] = &[
    k!(DIES, 1300.0, 0.45, 0.55, PkgState { stacks: 4.0, explode: 1.0, ..DIE_ONLY }).labels(&[(P::Logic, "logic die"), (P::Hbm, "HBM")]).notes(P::Logic, Some(P::Hbm)),
    k!([0.0, 100.0, 0.0], 3800.0, 0.35, 0.55, PkgState { explode: 0.6, ..WAFER }).labels(&[(P::Interposer, "interposer wafer")]).notes(P::Interposer, Some(P::Logic)),
    k!([0.0, 100.0, 0.0], 3800.0, 0.35, 0.55, PkgState { stacks: 4.0, ..WAFER }).labels(&[(P::Hbm, "stacks bonded")]).notes(P::Hbm, None),
    k!(PKG, 2300.0, 0.40, 0.30, PkgState { explode: 0.5, c4: 1.0, board: 0.0, bga: 0.0, ..BASE }).labels(&[(P::Substrate, "onto the substrate")]).notes(P::Substrate, Some(P::C4)),
    k!(PKG, 1900.0, 0.40, 0.15, PkgState { underfill: 1.0, cut: 1.0, c4: 1.0, ubump: 1.0, board: 0.0, bga: 0.0, ..BASE }).labels(&[(P::Underfill, "underfill")]).notes(P::Underfill, None),
    k!(PKG, 2300.0, 0.45, 0.35, PkgState { lid: 1.0, power: 0.8, data: 0.8, board: 0.0, bga: 0.0, ..BASE }).labels(&[(P::Lid, "lid"), (P::Logic, "under test")]).notes(P::Lid, Some(P::Logic)),
    k!([0.0, 100.0, 0.0], 4200.0, 0.40, 0.45, PkgState { lid: 1.0, count: 3.0, ..BASE }).labels(&[(P::Lid, "finished packages")]).notes(P::Lid, None),
];
const AA_B: &[Beat] = &[
    Beat::new("dies onto an uncut wafer", BEAT_MS).note("Placed face down at wafer scale.", "Interposers in a row.").detail("CHIP ON WAFER.", &["CoW"]),
    Beat::new("all dies placed", BEAT_MS).note("Logic and HBM on every site.", "Dies on every interposer.").detail("Microbumps.", &["Placed"]),
    Beat::new("thinned to reveal TSVs", BEAT_MS).note("Underfilled, molded, then the wafer is thinned.", "The wafer.").detail("TSVs open on the back.", &["Thin"]),
];
const AA_K: &[PkgKey] = &[
    k!([0.0, 100.0, 0.0], 3800.0, 0.35, 0.55, PkgState { explode: 0.6, ..WAFER }).title("chip on wafer", "face down"),
    k!([0.0, 100.0, 0.0], 3800.0, 0.35, 0.55, PkgState { stacks: 4.0, ..WAFER }).title("all placed", "logic + HBM"),
    k!([0.0, 100.0, 0.0], 3600.0, 0.35, 0.40, PkgState { stacks: 4.0, underfill: 1.0, ..WAFER }).title("thinned", "TSVs revealed"),
];
const AB_B: &[Beat] = &[
    Beat::new("cut into interposers", BEAT_MS).note("The wafer is diced.", "One interposer.").detail("Each with its dies.", &["Dice"]),
    Beat::new("C4 REFLOW onto the substrate", BEAT_MS).note("Bonded to an organic substrate.", "The interposer settles down.").detail("ON SUBSTRATE.", &["oS"]),
    Beat::new("underfilled", BEAT_MS).note("Epoxy wicks in.", "Underfill.").detail("UNDERFILL FLOW.", &["Underfill"]),
];
const AB_K: &[PkgKey] = &[
    k!(PKG, 1900.0, 0.45, 0.45, IP).title("diced", "one interposer"),
    k!(PKG, 2300.0, 0.40, 0.30, PkgState { explode: 0.0, c4: 1.0, board: 0.0, bga: 0.0, ..BASE }).title("on substrate", "C4 reflow"),
    k!(PKG, 1900.0, 0.40, 0.15, PkgState { underfill: 1.0, cut: 1.0, c4: 1.0, ubump: 1.0, board: 0.0, bga: 0.0, ..BASE }).title("underfill", "cured"),
];
const AC_B: &[Beat] = &[
    Beat::new("one part at 99%", BEAT_MS).note("A single die at 99% yield.", "One die.").detail("Illustrative.", &["99%"]),
    Beat::new("ten parts multiply", BEAT_MS).note("Logic, 8 HBM, interposer: 0.99^10 is about 90%.", "The full package.").detail("YIELD STACKUP.", &["~90%"]),
    Beat::new("why known-good dies matter", BEAT_MS).note("A late failure scraps everything; test early.", "The package under test.").detail("TEST.", &["KGD"]),
];
const AC_K: &[PkgKey] = &[
    k!(DIES, 1200.0, 0.45, 0.55, DIE_ONLY).title("one part", "99%"),
    k!(PKG, 2300.0, 0.40, 0.55, PkgState { board: 0.0, bga: 0.0, ..CHIPLET }).title("ten parts", "~90%"),
    k!(PKG, 2300.0, 0.45, 0.35, PkgState { lid: 1.0, power: 0.8, data: 0.8, board: 0.0, bga: 0.0, ..BASE }).title("test", "early and often"),
];
const AD_B: &[Beat] = &[
    Beat::new("almost every AI accelerator uses CoWoS", BEAT_MS).note("So its capacity limits shipments.", "A finished package.").detail("Reports.", &["CAPACITY"]),
    Beat::new("bigger packages use more", BEAT_MS).note("Larger interposers fit fewer per wafer.", "A big package.").detail("Blackwell.", &["Per package"]),
    Beat::new("OSATs add capacity", BEAT_MS).note("ASE and Amkor take steps; UMC makes interposers.", "Packages in a row.").detail("OSAT.", &["OSAT"]),
];
const AD_K: &[PkgKey] = &[
    k!(PKG, FAR, 0.45, 0.40, PkgState { lid: 1.0, ..BASE }).title("capacity", "limits output"),
    k!(PKG, 2800.0, 0.40, 0.40, PkgState { isize: 1.5, lid: 1.0, ..CHIPLET }).title("bigger packages", "more capacity each"),
    k!([0.0, 100.0, 0.0], 4200.0, 0.40, 0.45, PkgState { lid: 1.0, count: 3.0, ..BASE }).title("OSATs", "ASE, Amkor"),
];
const AE_B: &[Beat] = &[
    Beat::new("wafer sort", BEAT_MS).note("Dies tested on the wafer.", "Bare dies.").detail("KGD.", &["Sort"]),
    Beat::new("after chip on wafer", BEAT_MS).note("Tested again on the interposer.", "Dies on interposers.").detail("Before the substrate.", &["Mid"]),
    Beat::new("final package test", BEAT_MS).note("The finished package, powered.", "Package under test.").detail("Last chance.", &["Final"]),
];
const AE_K: &[PkgKey] = &[
    k!(DIES, 1300.0, 0.45, 0.55, PkgState { stacks: 4.0, explode: 1.0, power: 0.6, ..DIE_ONLY }).title("wafer sort", "known-good dies"),
    k!([0.0, 100.0, 0.0], 3800.0, 0.35, 0.55, PkgState { stacks: 4.0, power: 0.6, ..WAFER }).title("chip-on-wafer test", "mid-flow"),
    k!(PKG, 2300.0, 0.45, 0.35, PkgState { lid: 1.0, power: 1.0, data: 1.0, board: 0.0, bga: 0.0, ..BASE }).title("final test", "the whole package"),
];
const A_Z: [ZoomData; 5] = [('a', "chip on wafer", AA_B, AA_K), ('b', "on substrate", AB_B, AB_K), ('c', "yield stackup", AC_B, AC_K), ('d', "capacity", AD_B, AD_K), ('e', "test at every stage", AE_B, AE_K)];
const A_S: [SecData; 9] = [(AA_B, AA_K), (AB_B, AB_K), (AA_B, AA_K), (AC_B, AC_K), (AD_B, AD_K), (AD_B, AD_K), (AE_B, AE_K), (AD_B, AD_K), (AC_B, AC_K)];
pkg_node!(A_ZOOMS, A_SECTIONS, A_Z, A_S);
pub static ASSEMBLY: PkgNode = PkgNode { page: "ASSEMBLY", beats: A_B, keys: A_K, zooms: &A_ZOOMS, zoom_data: &A_Z, sections: &A_SECTIONS, section_data: &A_S };

// =================================================================== BOARD

const B_B: &[Beat] = &[
    Beat::new("the package on its board", OVERVIEW_MS).note("The finished package solders to a module board through BGA balls.", "The package on a green board.").detail("~1 mm ball pitch.", &["BGA BALLS"]),
    Beat::new("BGA balls underneath", OVERVIEW_MS).note("A grid of solder balls joins substrate to board.", "Low view: the ball grid.").detail("All power and signals pass here.", &["BGA"]),
    Beat::new("power: hundreds of amps under a volt", OVERVIEW_MS).note("Regulators on the board feed current up through every level into the die.", "Yellow power climbs from the board.").detail("I x R drop at each stage.", &["POWER DELIVERY", "VRM"]),
    Beat::new("all of it becomes heat", OVERVIEW_MS).note("The die turns the power into heat that has to leave through the top.", "The die glows; heat rises.").detail("Packages heading to thousands of watts.", &["HEAT"]),
    Beat::new("lid and cold plate", OVERVIEW_MS).note("A lid spreads the heat into a copper cold plate.", "Lid and finned copper plate on top.").detail("COLD PLATE.", &["Cold plate"]),
    Beat::new("liquid cooling", OVERVIEW_MS).note("At AI densities coolant runs through the plate instead of air over fins.", "The cooled package, heat carried off.").detail("LIQUID COOLING.", &["Liquid"]),
    Beat::new("modules in a rack", OVERVIEW_MS).note("GPU links tie modules together; many fill a rack with power shelves and switches.", "Several packages on a board.").detail("See Power and Network+Cool tabs.", &["NVLINK", "RACK"]),
];
const B_K: &[PkgKey] = &[
    k!(PKG, FAR, 0.45, 0.35, BASE.spot(P::Board)).labels(&[(P::Board, "board"), (P::Bga, "BGA")]).notes(P::Board, Some(P::Bga)),
    k!(LOW, 1500.0, 0.40, 0.06, PkgState { explode: 0.6, ..BASE }.spot(P::Bga)).labels(&[(P::Bga, "~1 mm balls")]).notes(P::Bga, None),
    k!(PKG, FAR, 0.40, 0.25, PkgState { power: 1.0, ..BASE }).labels(&[(P::Board, "VRM side"), (P::Logic, "into the die")]).notes(P::Board, Some(P::Logic)),
    k!(PKG, FAR, 0.40, 0.35, HOT).labels(&[(P::Logic, "heat")]).notes(P::Logic, None),
    k!(PKG, 2600.0, 0.40, 0.30, PkgState { explode: 0.5, ..COOLED }).labels(&[(P::Cooler, "cold plate on lid")]).notes(P::Cooler, Some(P::Lid)),
    k!(PKG, 2600.0, 0.45, 0.35, COOLED).labels(&[(P::Cooler, "coolant")]).notes(P::Cooler, None),
    k!([0.0, 100.0, 0.0], 4500.0, 0.40, 0.40, PkgState { count: 3.0, ..COOLED }).labels(&[(P::Board, "module board")]).notes(P::Board, None),
];
const BA_B: &[Beat] = &[
    Beat::new("the package", BEAT_MS).note("Ready to mount.", "The package.").detail("BGA below.", &["Package"]),
    Beat::new("balls to the board", BEAT_MS).note("Reflowed onto the board.", "The ball grid.").detail("BGA BALLS.", &["BGA"]),
    Beat::new("on the MODULE", BEAT_MS).note("Mounted with power stages and connectors.", "On its board.").detail("MODULE.", &["Module"]),
];
const BA_K: &[PkgKey] = &[
    k!(PKG, FAR, 0.45, 0.40, PkgState { board: 0.0, ..BASE }).title("package", "ready"),
    k!(LOW, 1500.0, 0.40, 0.06, PkgState { explode: 0.6, ..BASE }.spot(P::Bga)).title("BGA", "~1 mm"),
    k!(PKG, FAR, 0.45, 0.35, BASE.spot(P::Board)).title("module", "board"),
];
const BB_B: &[Beat] = &[
    Beat::new("VRM beside the package", BEAT_MS).note("Regulators step down to under a volt.", "Power starts at the board.").detail("VRM.", &["VRM"]),
    Beat::new("up through every level", BEAT_MS).note("BGA, substrate, C4, interposer, microbumps.", "Power climbs.").detail("I x R each step.", &["Path"]),
    Beat::new("into the die", BEAT_MS).note("Hundreds of amps reach the transistors.", "Power into the die.").detail("See TOP METAL.", &["POWER DELIVERY"]),
];
const BB_K: &[PkgKey] = &[
    k!(LOW, 1800.0, 0.40, 0.15, PkgState { power: 1.0, ..BASE }.spot(P::Board)).title("VRM", "under a volt"),
    k!(PKG, 2000.0, 0.40, 0.10, PkgState { power: 1.0, explode: 0.6, c4: 1.0, ubump: 1.0, ..BASE }).title("power path", "every level"),
    k!(DIES, 1300.0, 0.40, 0.35, PkgState { power: 1.0, ..BASE }.spot(P::Logic)).title("into the die", "hundreds of amps"),
];
const BC_B: &[Beat] = &[
    Beat::new("heat from the die", BEAT_MS).note("All the power ends as heat.", "The die glows.").detail("HEAT.", &["Heat"]),
    Beat::new("COLD PLATE on the lid", BEAT_MS).note("Copper block pressed on the lid.", "Lid and plate.").detail("Spreads heat.", &["Cold plate"]),
    Beat::new("LIQUID COOLING", BEAT_MS).note("Coolant through the plate replaces air.", "Heat carried away.").detail("Thousands of watts ahead.", &["Liquid"]),
];
const BC_K: &[PkgKey] = &[
    k!(PKG, FAR, 0.40, 0.35, HOT).title("heat", "from the die"),
    k!(PKG, 2600.0, 0.40, 0.30, PkgState { explode: 0.5, ..COOLED }).title("cold plate", "on the lid"),
    k!(PKG, 2600.0, 0.45, 0.35, COOLED).title("liquid cooling", "coolant through the plate"),
];
const BD_B: &[Beat] = &[
    Beat::new("one module", BEAT_MS).note("One GPU package on its board.", "One package.").detail("MODULE.", &["Module"]),
    Beat::new("linked GPUs", BEAT_MS).note("NVLink lanes tie GPUs together through switches.", "Several packages.").detail("NVLINK.", &["Links"]),
    Beat::new("a rack", BEAT_MS).note("Many modules, power shelves, switches.", "A row of cooled packages.").detail("RACK.", &["Rack"]),
];
const BD_K: &[PkgKey] = &[
    k!(PKG, FAR, 0.45, 0.35, COOLED).title("module", "one GPU"),
    k!([0.0, 100.0, 0.0], 4200.0, 0.40, 0.40, PkgState { count: 2.0, data: 1.0, ..COOLED }).title("NVLink", "GPUs as one"),
    k!([0.0, 100.0, 0.0], 4800.0, 0.40, 0.40, PkgState { count: 3.0, ..COOLED }).title("rack", "many modules"),
];
const BE_B: &[Beat] = &[
    Beat::new("power keeps rising", BEAT_MS).note("Each generation draws more.", "A hot package.").detail("Delivery losses rise too.", &["Power"]),
    Beat::new("air runs out", BEAT_MS).note("Liquid cooling needs new infrastructure.", "A cooled package.").detail("Facilities.", &["Cooling"]),
    Beat::new("bigger packages, bigger boards", BEAT_MS).note("Larger packages mean larger boards and more warpage at assembly.", "A big package.").detail("Notes: power figures not sourced here.", &["Size"]),
];
const BE_K: &[PkgKey] = &[
    k!(PKG, FAR, 0.40, 0.35, HOT).title("rising power", "delivery losses"),
    k!(PKG, 2600.0, 0.45, 0.35, COOLED).title("cooling", "liquid needed"),
    k!(PKG, 2800.0, 0.40, 0.35, PkgState { isize: 1.5, warp: 0.6, ..CHIPLET }).title("bigger", "boards and warpage"),
];
const B_Z: [ZoomData; 5] = [('a', "BGA to the board", BA_B, BA_K), ('b', "power delivery", BB_B, BB_K), ('c', "cooling: cold plate and liquid", BC_B, BC_K), ('d', "modules, links and racks", BD_B, BD_K), ('e', "power, cooling and size limits", BE_B, BE_K)];
const B_S: [SecData; 9] = [(BA_B, BA_K), (BA_B, BA_K), (BB_B, BB_K), (BB_B, BB_K), (BC_B, BC_K), (BD_B, BD_K), (BD_B, BD_K), (BD_B, BD_K), (BE_B, BE_K)];
pkg_node!(B_ZOOMS, B_SECTIONS, B_Z, B_S);
pub static BOARD: PkgNode = PkgNode { page: "BOARD", beats: B_B, keys: B_K, zooms: &B_ZOOMS, zoom_data: &B_Z, sections: &B_SECTIONS, section_data: &B_S };
