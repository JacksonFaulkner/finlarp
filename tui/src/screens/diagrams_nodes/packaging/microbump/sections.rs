// PACKAGING tab, MICROBUMP: numbered sections 1-9. Section N illustrates heading N of
// diagrams_pages/PKG_MICROBUMP.txt, from the Blender scenes in tools/pbr3d/blender/pkg_microbump_sections.py (GLBs
// in tools/pbr3d/assets/pkg_microbump_section_<n>.glb). Three beats each. The Sources heading (10) is text only.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static S1: Cell = std::sync::OnceLock::new();
static S2: Cell = std::sync::OnceLock::new();
static S3: Cell = std::sync::OnceLock::new();
static S4: Cell = std::sync::OnceLock::new();
static S5: Cell = std::sync::OnceLock::new();
static S6: Cell = std::sync::OnceLock::new();
static S7: Cell = std::sync::OnceLock::new();
static S8: Cell = std::sync::OnceLock::new();
static S9: Cell = std::sync::OnceLock::new();

/// 1 what happens: microbumps; C4 and BGA; hybrid bonds.
const S1_B: &[Beat] = &[
    Beat::new("microbumps join the dies", BEAT_MS)
        .note(
            "Each die is joined face down to the interposer by a field of microbumps, copper pillars with solder caps on about 40 um centres. The cut runs through the front row.",
            "A close row of cut pillars under a purple die, standing on copper pads over the interposer's striped wiring.",
        )
        .detail("The densest solder joints in the package.", &["MICROBUMP ~40 um", "CU PILLAR"]),
    Beat::new("C4 and BGA below", BEAT_MS)
        .note(
            "Below the interposer, C4 bumps at about 150 um join it to the substrate, and BGA balls about a millimetre apart join the substrate to the board. Power climbs through all of them, with TSVs linking the levels.",
            "The camera drops through the stack: a row of grey C4 balls, the striped substrate with copper vias, then big BGA balls on the green board, with amber beads climbing.",
        )
        .detail("Each level is coarser than the one above.", &["C4 BUMP ~150 um", "TSV"]),
    Beat::new("hybrid bonds replace them", BEAT_MS)
        .note(
            "At 10 um pitch and below, the microbumps go: the die is bonded copper to copper and oxide to oxide straight onto the interposer, with no solder and no gap.",
            "The pillars vanish and the die drops onto a thin pale layer striped with copper pads.",
        )
        .detail("The next step in density.", &["HYBRID BOND <=10 um", "No solder"]),
];

/// 2 the parts: one microbump, layer by layer.
const S2_B: &[Beat] = &[
    Beat::new("solder and intermetallics", BEAT_MS)
        .note(
            "At the foot of the joint, tin-silver solder sits on the interposer's copper pad. Where solder meets metal, thin intermetallic layers form: copper-tin at the pad, nickel-tin under the pillar.",
            "One joint drawn ten times larger and cut open: a grey solder barrel between two thin bronze bands, on a brown copper pad.",
        )
        .detail("The intermetallics are what actually hold.", &["SnAg solder", "IMC: Cu6Sn5, Ni3Sn4"]),
    Beat::new("pillar, barrier, seed, pad", BEAT_MS)
        .note(
            "Above the solder, a nickel barrier stops tin eating the copper. The copper pillar itself is about 25 um wide. At the die it stands on a titanium-copper seed layer (the UBM) over an aluminium pad.",
            "Up the column: a grey nickel band, a tall brown copper pillar, then a thin seed layer and a pale pad under the die.",
        )
        .detail("Each layer has one job.", &["CU PILLAR ~25 um", "UBM over Al pad"]),
    Beat::new("what it connects", BEAT_MS)
        .note(
            "The joint links the die's BEOL wiring, through a polyimide passivation opening, to the interposer's RDL and a TSV that drops through the silicon.",
            "Pulled back: the die slab on top with copper wiring stripes and an amber passivation layer, the joint, and below it an RDL wire and a copper TSV in the grey silicon.",
        )
        .detail("Die wiring to interposer wiring in one step.", &["RDL", "TSV"]),
];

/// 3 making a joint, in order.
const S3_B: &[Beat] = &[
    Beat::new("1-2 plate the pillars, cap them", BEAT_MS)
        .note(
            "Copper pillars are electroplated on the die's pads while it is still a wafer, and solder caps are plated on top.",
            "A die face down above a slab; copper beads build the pillars, then grey beads form domes on their tips.",
        )
        .detail("Done at wafer level, thousands at once.", &["CU PILLAR", "Solder cap"]),
    Beat::new("3-4 place and reflow", BEAT_MS)
        .note(
            "The die is placed face down so each pillar lands on its pad, then heated until the solder melts into joints.",
            "The die lowers onto the pads; the caps glow orange as they melt and settle into joints.",
        )
        .detail("About 250 C for tin-silver.", &["Flip-chip", "REFLOW"]),
    Beat::new("5 underfill", BEAT_MS)
        .note(
            "Epoxy underfill flows into the gap by capillary action and cures.",
            "Dark fill spreads between the pillars from one edge.",
        )
        .detail("The joint is finished.", &["UNDERFILL", "Cure"]),
];

/// 4 bump pitch: from C4 to hybrid bonds.
const S4_B: &[Beat] = &[
    Beat::new("three pitches, one scale", BEAT_MS)
        .note(
            "C4 at about 150 um, microbumps at about 40 um, hybrid bonds at 10 um and below, drawn at the same scale.",
            "A big cut ball, a slim pillar and a thin strip of tiny copper pads side by side.",
        )
        .detail("Each step is a new technology.", &["C4 ~150 um", "Microbump ~40 um", "Hybrid <=10 um"]),
    Beat::new("halve the pitch: 4x the joints", BEAT_MS)
        .note(
            "Two squares of the same size: at one pitch they hold 16 pads, at half the pitch 64. Density goes with one over the pitch squared.",
            "Seen from above, a pale square with a 4x4 grid of copper dots next to one with an 8x8 grid.",
        )
        .detail("Density is what buys bandwidth.", &["BUMP PITCH", "16 > 64"]),
    Beat::new("the solder wall", BEAT_MS)
        .note(
            "Shrink the pitch far enough and the solder caps touch when they melt. Microbumps are expected to hit this wall near 10 um.",
            "Two rows of balls; in the back row they touch and red bridges glow between them.",
        )
        .detail("Past here, hybrid bonding takes over.", &["Solder bridging", "~10 um"]),
];

/// 5 why hybrid bonding.
const S5_B: &[Beat] = &[
    Beat::new("polish both faces", BEAT_MS)
        .note(
            "Each face is copper pads set in oxide, polished flat by CMP. The copper is left dished a few nanometres below the oxide on purpose.",
            "Two cut-open blocks apart, upper and lower, each a pale oxide layer with brown copper pads; a cyan bead sweeps the surface.",
        )
        .detail("Flatness is measured in nanometres.", &["CMP", "Dished Cu pads"]),
    Beat::new("oxide bonds at room temperature", BEAT_MS)
        .note(
            "The faces are pressed together. The oxide surfaces bond to each other at room temperature, holding the dies while the copper pads still have a tiny gap.",
            "The upper block lowers onto the lower; a thin green line glows along the joined oxide.",
        )
        .detail("No solder and no gap between the dies.", &["Oxide-oxide bond", "Room temperature"]),
    Beat::new("anneal: copper closes the gap", BEAT_MS)
        .note(
            "An anneal heats the stack. Copper expands more than oxide, so the dished pads swell into each other and fuse into continuous copper joints.",
            "Heat rises through the block; a warm seam glows where each pair of copper pads meets.",
        )
        .detail("TSMC's SoIC stacks dies this way.", &["HYBRID BOND", "SoIC"]),
];

/// 6 underfill and stress.
const S6_B: &[Beat] = &[
    Beat::new("the die heats", BEAT_MS)
        .note(
            "Under load the die heats the package. Silicon expands about 3 ppm per degree and the organic substrate several times that.",
            "A small cut-away package with heat rising off the purple die.",
        )
        .detail("The levels want different sizes.", &["CTE mismatch", "Si ~3 ppm/C"]),
    Beat::new("the corners take the shear", BEAT_MS)
        .note(
            "The substrate grows more and bows; the outermost joints move furthest and take the most shear, cycle after cycle.",
            "Close on the package edge: the substrate bends and the end C4 ball glows red.",
        )
        .detail("Fatigue starts at the corners.", &["WARPAGE", "Shear strain"]),
    Beat::new("underfill locks the levels", BEAT_MS)
        .note(
            "Underfill under the die and under the interposer bonds the levels together, spreading the strain across the whole area. For C4 joints it gives over ten times the thermal-cycle life.",
            "Dark underfill fills both gaps and the red glow is gone.",
        )
        .detail("UCLA Pb-free workshop (Totta).", &["UNDERFILL", ">10x C4 cycle life"]),
];

/// 7 current and electromigration.
const S7_B: &[Beat] = &[
    Beat::new("thousands of power bumps", BEAT_MS)
        .note(
            "The die's power enters through thousands of bumps, each carrying a small share of hundreds of amps.",
            "One joint drawn large and cut open with blue electron beads streaming down through it.",
        )
        .detail("Power, not signals, takes most bump sites.", &["Power bumps", "Current per bump"]),
    Beat::new("electromigration", BEAT_MS)
        .note(
            "The electron flow pushes metal atoms along with it. Atoms pile up downstream and leave a void where the current enters the solder, near the intermetallic layer.",
            "Close on the top of the solder: a dark void spreads along the thin bronze band.",
        )
        .detail("Smaller bumps raise current density.", &["ELECTROMIGRATION", "Void at the cathode"]),
    Beat::new("split the current", BEAT_MS)
        .note(
            "More bumps share the load, so the density in each falls below where voids grow.",
            "A row of six smaller joints beside the big one, each with a thin stream of beads.",
        )
        .detail("Bump count is part of the power budget.", &["More bumps", "Lower density each"]),
];

/// 8 who makes it.
const S8_B: &[Beat] = &[
    Beat::new("TSMC and the memory makers", BEAT_MS)
        .note(
            "TSMC (TSM) builds the CoWoS interposer and bonds the dies to it on microbumps. The HBM stacks, with their own microbumps between DRAM layers, come from SK hynix, Micron and Samsung.",
            "The package from above the front corner, tags on the interposer, the logic die's microbumps and the blue HBM stack.",
        )
        .detail("CoWoS capacity has gated AI GPU supply.", &["TSMC (TSM): CoWoS", "HBM: SK hynix, Micron, Samsung"]),
    Beat::new("bumping and flip-chip", BEAT_MS)
        .note(
            "ASE (ASX) and Amkor (AMKR) do wafer bumping, flip-chip assembly and test. The ABF substrates under the C4 bumps come from makers such as Ibiden and Unimicron.",
            "Lower in the stack: tags on the C4 row, the green-and-tan substrate and the BGA balls.",
        )
        .detail("The OSATs bump and assemble most chips.", &["ASE (ASX)", "Amkor (AMKR)"]),
    Beat::new("hybrid bonding", BEAT_MS)
        .note(
            "TSMC's SoIC uses hybrid bonds for die-on-die stacking. Besi and others make the hybrid bonding tools (not sourced here).",
            "The die sits flat on its hybrid-bond layer, tagged.",
        )
        .detail("The tool makers gain as pitch shrinks.", &["SoIC", "Besi (not sourced)"]),
];

/// 9 chokepoints and risks.
const S9_B: &[Beat] = &[
    Beat::new("solder bridging", BEAT_MS)
        .note(
            "Below about 10 um pitch, molten solder bridges neighbouring bumps and shorts them. This is what forces the move to hybrid bonding.",
            "A tight row of solder balls on a pale slab, a red glowing bridge joining them.",
        )
        .detail("A hard wall for solder.", &["Bridging", "~10 um"]),
    Beat::new("flatness and particles", BEAT_MS)
        .note(
            "Hybrid bonds need near-perfect flatness and cleanliness. One particle between the faces holds them apart and leaves an unbonded void around it, killing every pad nearby.",
            "Two bonded blocks held slightly apart by a red speck; a dark gap spreads along the interface.",
        )
        .detail("Yield is the hard part of hybrid bonding.", &["Particle void", "Cleanroom grade surfaces"]),
    Beat::new("cracked joints", BEAT_MS)
        .note(
            "Thermal cycling without good underfill cracks joints, usually along the brittle intermetallic layer.",
            "One joint drawn large; a red crack runs along the bronze band at the top of the solder.",
        )
        .detail("Underfill and IMC control set the lifetime.", &["Thermal fatigue", "IMC crack"]),
];

fn section_1() -> Box<dyn Scene> {
    page(&S1, include_bytes!("../../../../../../tools/pbr3d/assets/pkg_microbump_section_1.glb"), S1_B)
}

fn section_2() -> Box<dyn Scene> {
    page(&S2, include_bytes!("../../../../../../tools/pbr3d/assets/pkg_microbump_section_2.glb"), S2_B)
}

fn section_3() -> Box<dyn Scene> {
    page(&S3, include_bytes!("../../../../../../tools/pbr3d/assets/pkg_microbump_section_3.glb"), S3_B)
}

fn section_4() -> Box<dyn Scene> {
    page(&S4, include_bytes!("../../../../../../tools/pbr3d/assets/pkg_microbump_section_4.glb"), S4_B)
}

fn section_5() -> Box<dyn Scene> {
    page(&S5, include_bytes!("../../../../../../tools/pbr3d/assets/pkg_microbump_section_5.glb"), S5_B)
}

fn section_6() -> Box<dyn Scene> {
    page(&S6, include_bytes!("../../../../../../tools/pbr3d/assets/pkg_microbump_section_6.glb"), S6_B)
}

fn section_7() -> Box<dyn Scene> {
    page(&S7, include_bytes!("../../../../../../tools/pbr3d/assets/pkg_microbump_section_7.glb"), S7_B)
}

fn section_8() -> Box<dyn Scene> {
    page(&S8, include_bytes!("../../../../../../tools/pbr3d/assets/pkg_microbump_section_8.glb"), S8_B)
}

fn section_9() -> Box<dyn Scene> {
    page(&S9, include_bytes!("../../../../../../tools/pbr3d/assets/pkg_microbump_section_9.glb"), S9_B)
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
