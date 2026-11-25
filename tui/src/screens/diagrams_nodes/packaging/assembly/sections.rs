// PACKAGING tab, ASSEMBLY: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/PKG_ASSEMBLY.txt,
// from the Blender scenes in tools/pbr3d/blender/pkg_assembly_sections.py (GLBs in
// tools/pbr3d/assets/pkg_assembly_section_<n>.glb). Three beats each. The Sources heading (10) is text only.

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

/// 1 what happens: chip on wafer; cut apart; on substrate.
const S1_B: &[Beat] = &[
    Beat::new("CHIP ON WAFER", BEAT_MS)
        .note(
            "Assembly starts on a whole interposer wafer. Known-good logic dies and HBM stacks are bonded face down onto every site before anything is cut.",
            "A grey wafer covered in sites, each with a purple die and four orange stacks; at the front edge one site is cut open and its microbumps glow.",
        )
        .detail("Bonding at wafer scale is precise and fast.", &["CHIP ON WAFER", "Every site filled first"]),
    Beat::new("the wafer is cut apart", BEAT_MS)
        .note(
            "After underfill, mold and thinning, blades cut the wafer along its streets. Each piece is one interposer with its dies, ready for the next stage.",
            "Two dicing blades run down the streets either side of the hero site; the wafer vanishes and the cut-out piece rises alone.",
        )
        .detail("One cut-out, one future package.", &["Dicing", "Interposer + its dies"]),
    Beat::new("ON SUBSTRATE", BEAT_MS)
        .note(
            "The cut-out lands on an organic substrate. Reflow melts its C4 bumps into joints, and underfill wicks in beneath it.",
            "The piece settles on a tan and green substrate with copper in its cut face; the C4 row glows, then black underfill spreads under it.",
        )
        .detail("Chip on wafer on substrate: CoWoS.", &["ON SUBSTRATE", "C4 REFLOW + UNDERFILL"]),
];

/// 2 the parts: substrate, interposer, top level.
const S2_B: &[Beat] = &[
    Beat::new("the substrate level", BEAT_MS)
        .note(
            "At the bottom, BGA balls will join the board. The substrate above them is a stiff glass-cloth core with plated through-holes, wrapped in ABF build-up layers that carry fine copper wiring up to the C4 bumps.",
            "A close cut face: grey balls along the bottom, a tan and olive band of layers striped with copper lines, copper columns through the middle, and silver C4 balls on top; yellow beads climb through it.",
        )
        .detail("The substrate fans fine pitch out to board pitch.", &["BGA, ABF build-up, core", "C4 bumps on top"]),
    Beat::new("the interposer level", BEAT_MS)
        .note(
            "The silicon interposer carries copper TSVs straight through it and three levels of fine copper wiring (the RDL) on top. Microbumps under the dies sit in underfill on that wiring.",
            "A grey silicon band with evenly spaced copper columns, a thin blue-grey top layer threaded with copper lines, and tiny bumps above; a cyan bead runs along the top layer.",
        )
        .detail("Silicon allows wiring far finer than any substrate.", &["TSVs + 3-level RDL", "Microbumps in underfill"]),
    Beat::new("die, HBM, mold, TIM, lid", BEAT_MS)
        .note(
            "On top, the logic die sits metal-side down, with HBM stacks of a base die and eight DRAM dies beside it. Mold fills the gaps, a TIM sheet covers them and the copper lid closes the package.",
            "The purple die glowing amber, orange stacks striped with layers and copper TSVs, grey mold between, a silver sheet above and the brown lid; orange beads rise through the lid.",
        )
        .detail("Everything that makes heat sits under the lid.", &["HBM: base + 8 DRAM", "Mold, TIM, lid"]),
];

/// 3 in order: place and bond; underfill, mold, thin; substrate, underfill, lid.
const S3_B: &[Beat] = &[
    Beat::new("1 place and bond", BEAT_MS)
        .note(
            "The logic die drops face down onto the bare interposer and bonds; then the HBM stacks land beside it, one at a time.",
            "A bare interposer slab; the purple die falls onto it, then four orange stacks drop around it.",
        )
        .detail("Logic first, memory beside it.", &["Step 1: place + bond", "Die, then 4 stacks"]),
    Beat::new("2 underfill, mold, thin", BEAT_MS)
        .note(
            "Underfill wicks under the dies and mold fills between them. Then the wafer is thinned and C4 bumps are formed on the revealed TSVs.",
            "Black underfill spreads under the dies, a grey mold frame drops between them, and a row of silver bumps appears under the interposer.",
        )
        .detail("Lock the joints, then open the back.", &["Step 2: underfill + mold", "Thin, then C4 bumps"]),
    Beat::new("3-5 cut, substrate, lid", BEAT_MS)
        .note(
            "The cut interposer is reflowed onto the substrate and underfilled again. A TIM sheet and lid go on, and the package is tested and shipped.",
            "The block lowers onto a substrate, the C4 row glows, black underfill spreads, and a silver sheet and copper lid drop on top.",
        )
        .detail("Five steps, each one a chance to fail.", &["Steps 3-4: cut, ON SUBSTRATE", "Step 5: lid, TEST, ship"]),
];

/// 4 yield: one part, ten parts, one failure.
const S4_B: &[Beat] = &[
    Beat::new("one part at 99%", BEAT_MS)
        .note(
            "Suppose each part comes out good 99% of the time. The logic die alone is a 99% bet.",
            "The package cut open without its lid; the logic die's band on the cut face lights green.",
        )
        .detail("Illustrative figure.", &["One part: 99%", "Tested logic die"]),
    Beat::new("ten parts multiply", BEAT_MS)
        .note(
            "The package needs all of them: die, stacks, bumps, interposer, wiring, C4 joints, substrate and balls. Ten 99% parts give 0.99 to the tenth, about 90%.",
            "The bands light green one after another down the cut face until the whole package glows green.",
        )
        .detail("YIELD STACKUP multiplies.", &["0.99^10 = ~90%", "x 10 parts and joints"]),
    Beat::new("one fails, all scrapped", BEAT_MS)
        .note(
            "When one HBM stack fails, every other good part in the package goes with it. That is why only known-good dies are assembled.",
            "One stack's band turns red, then every band turns red.",
        )
        .detail("A late failure is the costliest failure.", &["One stack fails", "KNOWN-GOOD DIES only"]),
];

/// 5 capacity: sites per wafer and the line.
const S5_B: &[Beat] = &[
    Beat::new("one wafer, ~15-20 big packages", BEAT_MS)
        .note(
            "A 300 mm interposer wafer has room for only about 15 to 20 of the largest CoWoS interposers. Each site lights as it fills.",
            "A full round wafer from above, ruled into big squares; die-and-stack sites appear one by one.",
        )
        .detail("Big packages use a lot of wafer.", &["300 mm wafer", "~15-20 big sites"]),
    Beat::new("bigger means fewer", BEAT_MS)
        .note(
            "Halve the interposer's sides and four times as many fit on the same wafer. Larger accelerator packages eat more capacity per unit.",
            "Two wafers side by side: the left with a few large sites, the right packed with many small dies.",
        )
        .detail("Package size and capacity trade off.", &["Big: ~2.5-3.3x reticle", "Half the side: ~4x as many"]),
    Beat::new("the line sets the output", BEAT_MS)
        .note(
            "CoWoS capacity is counted in wafers a month, and every package on the line used part of one. That rate, not wafer supply, has capped AI accelerator shipments.",
            "A conveyor belt carries lidded packages through a grey gate.",
        )
        .detail("Capacity is the bottleneck.", &["CAPACITY: wafers a month", "Packages, not wafers"]),
];

/// 6 OSAT: who does which half.
const S6_B: &[Beat] = &[
    Beat::new("TSMC does chip on wafer", BEAT_MS)
        .note(
            "The front half, chip on wafer, needs wafer-fab tools, so TSMC does most of it. Interposer wafers come from TSMC, and UMC also supplies some.",
            "A wafer on a dark factory floor, with purple dies and orange stacks on its sites.",
        )
        .detail("The fine-pitch half stays at the foundry.", &["TSMC: CoW", "Interposers: TSMC, UMC"]),
    Beat::new("the cut parts ship out", BEAT_MS)
        .note(
            "Cut chip-on-wafer parts can be shipped to an outsourced assembly and test house for the back half.",
            "A grey crate stacked with silicon pieces slides from the wafer floor toward a second floor as cyan beads lead the way.",
        )
        .detail("Splitting the flow adds capacity.", &["Cut parts ship", "To an OSAT"]),
    Beat::new("ASE / Amkor: ON SUBSTRATE and TEST", BEAT_MS)
        .note(
            "OSATs such as ASE and Amkor bond the parts onto substrates, add the lid and run final test.",
            "On the second floor the package sits on its substrate, its C4 row glowing, then in a test socket with beads running through it.",
        )
        .detail("The back half can move to OSATs.", &["ASE (ASX), Amkor (AMKR)", "oS + TEST"]),
];

/// 7 test: sort, after chip on wafer, final.
const S7_B: &[Beat] = &[
    Beat::new("WAFER SORT", BEAT_MS)
        .note(
            "Every logic die is probed on its own wafer. Passing dies are known-good; failing ones are never assembled.",
            "A probe card over a wafer of purple dies; its needles touch one die, which lights green, while a neighbour lights red.",
        )
        .detail("Cheapest place to find a bad die.", &["Probe every die", "Fail: never assembled"]),
    Beat::new("after chip on wafer", BEAT_MS)
        .note(
            "With the dies bonded, the site can be probed through pads on the interposer to check the die-to-HBM links before the costly substrate step.",
            "A probe card hovers over the interposer's edge pads beside the bonded die and stacks; cyan beads cross between stack and die.",
        )
        .detail("Catch bad bonds before they get a substrate.", &["TEST after CoW", "Links checked"]),
    Beat::new("final TEST", BEAT_MS)
        .note(
            "The finished package runs in a socket at full power and speed, and burn-in shakes out parts that would fail early.",
            "The lidded package in a dark socket on pogo pins, with power, data and heat beads all flowing and the die glowing.",
        )
        .detail("Last chance before the customer.", &["Final test socket", "Burn-in"]),
];

/// 8 who makes it: the stack, layer by layer.
const S8_B: &[Beat] = &[
    Beat::new("dies, HBM and lid", BEAT_MS)
        .note(
            "The package opens into its layers. TSMC makes the logic dies for NVIDIA and AMD; SK hynix, Samsung and Micron make the HBM stacks.",
            "The package rises apart into layers: substrate, interposer, the die and stacks, the TIM and the lid floating above.",
        )
        .detail("Many makers inside one package.", &["Logic: TSMC", "HBM: SK hynix, Samsung, Micron"]),
    Beat::new("interposer and assembly", BEAT_MS)
        .note(
            "TSMC does most CoWoS assembly; UMC also makes interposer wafers. Bonding tools come from makers such as BESI, ASMPT and Hanmi (reports).",
            "The interposer layer and the die level, with their bumps, in the middle of the exploded stack.",
        )
        .detail("Assembly is concentrated at TSMC.", &["CoWoS: TSMC", "Interposers: TSMC, UMC"]),
    Beat::new("substrate and OSATs", BEAT_MS)
        .note(
            "ABF substrates come from Ibiden, Unimicron and others, built on Ajinomoto's ABF film. ASE and Amkor do on-substrate assembly and test.",
            "The substrate and its BGA balls at the bottom of the exploded stack.",
        )
        .detail("The substrate is its own supply chain.", &["ABF film: Ajinomoto", "oS + test: ASE, Amkor"]),
];

/// 9 chokepoints: capacity, warpage, late defects.
const S9_B: &[Beat] = &[
    Beat::new("capacity: one gate", BEAT_MS)
        .note(
            "Packages queue for a limited line, and one supplier does most CoWoS. Shipments follow its monthly capacity.",
            "Small packages bunch up behind a grey gate on a conveyor while one passes through.",
        )
        .detail("Concentration is the risk.", &["CAPACITY", "One main supplier"]),
    Beat::new("warpage at reflow", BEAT_MS)
        .note(
            "Silicon and organic substrate expand differently when heated. A big package bows at reflow, and the joints at its edges crack.",
            "The C4 row glows, then the substrate bows into a curve and red marks appear at the outermost joints.",
        )
        .detail("Bigger packages warp more.", &["Warpage", "Edge joints crack"]),
    Beat::new("a late defect scraps it all", BEAT_MS)
        .note(
            "A fault found at final test throws away the die, the HBM and the substrate together.",
            "One stack's band turns red, then the whole cut face turns red.",
        )
        .detail("Every step must be near perfect.", &["Found at final test", "Everything scrapped"]),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_assembly_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_assembly_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_assembly_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_assembly_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_assembly_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_assembly_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_assembly_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_assembly_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_assembly_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sections_have_three_explained_beats() {
        for (i, s) in SECTIONS.iter().enumerate() {
            let s = s();
            let what = format!("section {}", i + 1);
            assert_eq!(s.beats().len(), 3, "{what}");
            super::super::super::super::blender::explained(s.as_ref(), &what);
            super::super::super::super::blender::draws_every_beat(s.as_ref(), &what);
        }
    }
}
