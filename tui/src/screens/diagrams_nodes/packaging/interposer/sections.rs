// PACKAGING tab, INTERPOSER: numbered sections 1-9. Section N illustrates heading N of
// diagrams_pages/PKG_INTERPOSER.txt, from the Blender scenes in tools/pbr3d/blender/pkg_interposer_sections.py
// (GLBs tools/pbr3d/assets/pkg_interposer_section_<n>.glb). Three beats each. The Sources heading (10) is text only.

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

/// 1 what happens: the package cut open; data across the interposer; power up through it.
const S1_B: &[Beat] = &[
    Beat::new("a slab under the GPU and its HBM", BEAT_MS)
        .note(
            "The interposer sits under the GPU die and its HBM stacks and over the package substrate. Everything the dies say to each other, and everything they draw from the board, passes through it.",
            "The package cut open: board, substrate, silver C4 balls, the grey interposer, and the purple die between two striped orange stacks.",
        )
        .detail("TSMC calls the assembly CoWoS.", &["CoWoS", "Interposer"]),
    Beat::new("thousands of wires between them", BEAT_MS)
        .note(
            "Data runs between each stack and the GPU through the interposer's fine copper wiring, never leaving the package.",
            "Close on the right stack and the die edge: cyan beads drop into the interposer's top band, run left and rise into the die.",
        )
        .detail("All inside the slab.", &["WIRING DENSITY", "1,024 bits per HBM3 stack"]),
    Beat::new("power passes down through it", BEAT_MS)
        .note(
            "Power and the remaining signals cross the interposer vertically through TSVs, to and from the C4 bumps and the substrate.",
            "Yellow beads climb from the board through the substrate, the C4 balls and the copper columns in the silicon.",
        )
        .detail("TSVs link the top wiring to the C4s.", &["TSV", "C4 bumps"]),
];

/// 2 the parts: CoWoS-S, TSV and BEOL; CoWoS-L and its bridge; the BEOL up close.
const S2_B: &[Beat] = &[
    Beat::new("CoWoS-S: silicon, TSVs, wiring", BEAT_MS)
        .note(
            "In CoWoS-S the interposer is all silicon: a body crossed by TSVs, four levels of copper wiring on top, and microbumps up to the dies.",
            "The left half of the cut: the grey silicon with copper columns, the pale wiring band with copper dashes, and a row of short pillars under the die.",
        )
        .detail("The classic silicon interposer.", &["COWOS-S", "TSV", "RDL / BEOL"]),
    Beat::new("CoWoS-L: organic slab, silicon bridge", BEAT_MS)
        .note(
            "In CoWoS-L the slab is organic: polymer layers with copper lines, copper pillars instead of TSVs, and a small silicon bridge chip under each joint.",
            "Close on the right seam: a cyan bridge chip sunk in the dark slab under the gap between die and stack, with cyan beads crossing through it.",
        )
        .detail("Silicon only under the joints.", &["COWOS-L", "LSI BRIDGE"]),
    Beat::new("the wiring stack up close", BEAT_MS)
        .note(
            "Drawn large, the wiring is four copper levels in oxide joined by vias. The bottom two carry the finest lines; the top two are wider for longer runs. A pad and a copper pillar sit on top.",
            "A block of pale oxide with rows of copper bars getting wider toward the top, short copper vias between them, and a copper pillar with a silver cap; cyan beads run down and across.",
        )
        .detail("Lines get wider as they climb.", &["M1-M2 finest", "M3-M4 wider"]),
];

/// 3 in order: out of the HBM; through the wiring stack; up into the GPU while power climbs.
const S3_B: &[Beat] = &[
    Beat::new("1 out of the HBM base die", BEAT_MS)
        .note(
            "The data leaves the HBM's base die through a microbump into the interposer.",
            "Close on the stack's blue base die: cyan beads drop through the copper pillars below it.",
        )
        .detail("Step one of five.", &["HBM base die", "Microbump"]),
    Beat::new("2 down the stack and across", BEAT_MS)
        .note(
            "Inside the interposer it steps down through vias to a lower copper level and runs sideways toward the GPU.",
            "The wiring stack drawn large: cyan beads come down the pillar, step down the vias and run along a copper bar.",
        )
        .detail("Lower levels carry the fine lines.", &["Vias", "Across M2"]),
    Beat::new("3 into the GPU, 4 power up, 5 in parallel", BEAT_MS)
        .note(
            "It rises through a microbump into the GPU. Power climbs the other way, up the TSVs from the substrate. And thousands of these wires run side by side.",
            "Back on the package: cyan beads from both stacks into the die, and yellow beads climbing through the TSVs underneath.",
        )
        .detail("Steps three to five.", &["Into the GPU", "Power up the TSVs"]),
];

/// 4 CoWoS-S: the silicon slab; one TSV cut open; ~3.3 reticles from above.
const S4_B: &[Beat] = &[
    Beat::new("one silicon slab", BEAT_MS)
        .note(
            "CoWoS-S is a single silicon slab about 100 um thick, its wiring made in a fab on a mature node.",
            "The left of the cut-away: the grey slab, its pale wiring band and copper columns, on silver balls.",
        )
        .detail("Fab-made, so fine.", &["COWOS-S", "Mature node"]),
    Beat::new("a TSV cut open", BEAT_MS)
        .note(
            "Each TSV is copper in a hole through the silicon, with an oxide liner to insulate it and a barrier to keep the copper out of the silicon.",
            "One TSV drawn large and cut in half: copper core, thin dark barrier, white liner; yellow beads climb through it.",
        )
        .detail("Liner, barrier, fill.", &["TSV", "Oxide liner"]),
    Beat::new("up to ~3.3 reticles", BEAT_MS)
        .note(
            "TSMC lists CoWoS-S up to about 3.3 reticles, about 2,700 mm2, with room for one large die and its stacks. Beyond that it points to CoWoS-L or CoWoS-R.",
            "From above: a CoWoS-S package, one die and four stacks, inside a 2x2 grid of glowing reticle outlines.",
        )
        .detail("TSMC's CoWoS page.", &["~3.3x reticle", "~2,700 mm2"]),
];

/// 5 CoWoS-L: the organic slab; an HBM bridge; the die-to-die bridge.
const S5_B: &[Beat] = &[
    Beat::new("an organic slab", BEAT_MS)
        .note(
            "CoWoS-L builds the interposer from polymer and copper layers on a moulded body, with copper pillars to carry power down. It is cheaper per area and can grow larger.",
            "The CoWoS-L cut-away: a dark slab with a tan wiring layer, copper pillars, cyan bridge chips at the seams, two purple dies.",
        )
        .detail("Cheaper, and it scales.", &["COWOS-L", "Organic RDL"]),
    Beat::new("a bridge under die and HBM", BEAT_MS)
        .note(
            "Where a stack meets the GPU, a small silicon bridge chip carries the fine wires the organic layers cannot draw.",
            "Close on the right seam: cyan beads leave the stack, cross through the cyan bridge's fine lines and rise into the die.",
        )
        .detail("Silicon only where it is needed.", &["LSI BRIDGE", "Die to HBM"]),
    Beat::new("a bridge between the dies", BEAT_MS)
        .note(
            "Another bridge sits under the seam between the two GPU dies, so they act as one chip. NVIDIA quotes about 10 TB/s across Blackwell's link.",
            "Close on the gap between the two purple dies: dense cyan beads cross from one die to the other through a bridge underneath.",
        )
        .detail("Tom's Hardware, TrendForce.", &["~10 TB/s die to die", "Blackwell"]),
];

/// 6 growing past the reticle: 3.3x; 9.5x with 12 stacks; fewer per wafer.
const S6_B: &[Beat] = &[
    Beat::new("today: ~3.3 reticles", BEAT_MS)
        .note(
            "Interposer size is counted as a reticle multiple. CoWoS-S tops out near 3.3.",
            "From above: a one-die package inside a 2x2 grid of glowing reticle outlines.",
        )
        .detail("The RETICLE MULTIPLE.", &["~3.3x", "858 mm2 per reticle"]),
    Beat::new("2027: ~9.5 reticles", BEAT_MS)
        .note(
            "TSMC plans 9.5-reticle interposers with 12 HBM stacks in 2027, and over 14 reticles with up to 24 HBM5E stacks by 2029.",
            "A far bigger organic package with two dies and twelve stacks inside a 4x3 grid of outlines.",
        )
        .detail("Tom's Hardware, TSMC roadmap.", &["9.5x, 12 HBM", ">14x by 2029"]),
    Beat::new("fewer per wafer", BEAT_MS)
        .note(
            "Bigger slabs mean fewer per 300 mm wafer: only about five of the 9.5-reticle size fit here, so each GPU takes more packaging capacity.",
            "A round wafer from above holding only a few large pale squares.",
        )
        .detail("More capacity per GPU.", &["~5 per wafer", "300 mm"]),
];

/// 7 why silicon wiring: silicon lines; organic RDL lines; substrate lines, one scale.
const S7_B: &[Beat] = &[
    Beat::new("silicon: ~0.4 um lines", BEAT_MS)
        .note(
            "Silicon wiring is drawn with chip-fab lithography, so lines and gaps can be well under a micron. Forty-nine copper lines fit in a 40 um strip.",
            "From above, a pale strip striped with dozens of thin copper lines; a cyan bead runs across them.",
        )
        .detail("Fab lithography.", &["~0.4 um lines", "49 in 40 um"]),
    Beat::new("organic RDL: ~2 um lines", BEAT_MS)
        .note(
            "Polymer redistribution layers manage lines of a couple of microns. The same strip holds about ten.",
            "A tan strip of the same width with ten copper lines.",
        )
        .detail("Cheaper, coarser.", &["~2 um lines", "10 in 40 um"]),
    Beat::new("substrate: ~10 um lines", BEAT_MS)
        .note(
            "The package substrate's build-up film carries lines around ten microns wide: two in the strip. A 1,024-bit bus per stack needs the silicon density.",
            "All three strips side by side at one scale: dense, medium, and two wide copper lines.",
        )
        .detail("Why the interposer exists.", &["~10 um lines", "WIRING DENSITY"]),
];

/// 8 who makes it: TSMC on the slab; OSATs on the assembly; capacity on the wafer.
const S8_B: &[Beat] = &[
    Beat::new("TSMC makes the slab", BEAT_MS)
        .note(
            "TSMC makes most CoWoS interposers and does most of the assembly, as well as the GPU die itself. UMC supplies some outsourced silicon interposers.",
            "The silicon package cut-away, tagged by maker on the slab, its wiring and the die.",
        )
        .detail("NVIDIA's 10-K names TSMC and CoWoS.", &["TSMC (TSM)", "UMC"]),
    Beat::new("OSATs assemble too", BEAT_MS)
        .note(
            "ASE (with SPIL) and Amkor build 2.5D packages on interposers and add assembly capacity. SK hynix, Samsung and Micron make the HBM.",
            "The CoWoS-L package from the other side, tagged with assembly and memory makers.",
        )
        .detail("ASE and Amkor filings list 2.5D / CoWoS.", &["ASE (ASX)", "Amkor (AMKR)"]),
    Beat::new("capacity is counted in wafers", BEAT_MS)
        .note(
            "CoWoS capacity is quoted in interposer wafers per month, and TSMC runs most of it, with OSATs taking overflow.",
            "A round wafer of pale interposer rectangles from above.",
        )
        .detail("Wafers per month.", &["TSMC most", "OSAT overflow"]),
];

/// 9 chokepoints: big slabs, few per wafer; one supplier, HBM beside it; heat and size.
const S9_B: &[Beat] = &[
    Beat::new("few big slabs per wafer", BEAT_MS)
        .note(
            "The biggest interposers leave only a handful per wafer, and the round edge wastes more as they grow.",
            "A wafer from above with just a few large squares.",
        )
        .detail("Size eats capacity.", &["~5 per wafer at 9.5x", "Edge loss"]),
    Beat::new("one supplier, and HBM beside it", BEAT_MS)
        .note(
            "One company does most of the work, and HBM supply is a second limit on every package. Cerebras' 2026 results call CoWoS and HBM supply-limited.",
            "The CoWoS-L package cut open, cyan beads crossing its bridges.",
        )
        .detail("Two limits on one package.", &["TSMC concentration", "HBM supply"]),
    Beat::new("heat and size", BEAT_MS)
        .note(
            "A larger slab carries more watts and warps more as it heats and cools, which strains the bumps and makes yield harder.",
            "The lidded package on its board; the dies glow and heat rises out of the lid.",
        )
        .detail("Warpage limits growth.", &["1,000 W+", "Warpage"]),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_interposer_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_interposer_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_interposer_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_interposer_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_interposer_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_interposer_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_interposer_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_interposer_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_interposer_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
