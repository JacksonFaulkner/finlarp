// PACKAGING tab, LOGIC DIE: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/PKG_LOGIC_DIE.txt,
// from the Blender scenes in tools/pbr3d/blender/pkg_logic_die_sections.py (GLBs tools/pbr3d/assets/
// pkg_logic_die_section_<n>.glb). Three beats each. The Sources heading (10) is text only.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

macro_rules! section {
    ($f:ident, $cell:ident, $file:literal, $beats:ident) => {
        static $cell: Cell = std::sync::OnceLock::new();
        fn $f() -> Box<dyn Scene> {
            page(&$cell, include_bytes!(concat!("../../../../../../tools/pbr3d/assets/", $file)), $beats)
        }
    };
}

section!(section_1, S1, "pkg_logic_die_section_1.glb", S1_B);
section!(section_2, S2, "pkg_logic_die_section_2.glb", S2_B);
section!(section_3, S3, "pkg_logic_die_section_3.glb", S3_B);
section!(section_4, S4, "pkg_logic_die_section_4.glb", S4_B);
section!(section_5, S5, "pkg_logic_die_section_5.glb", S5_B);
section!(section_6, S6, "pkg_logic_die_section_6.glb", S6_B);
section!(section_7, S7, "pkg_logic_die_section_7.glb", S7_B);
section!(section_8, S8, "pkg_logic_die_section_8.glb", S8_B);
section!(section_9, S9, "pkg_logic_die_section_9.glb", S9_B);

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];

/// 1 what happens: the die in its package; the reticle field round it; two dies and their HBM.
const S1_B: &[Beat] = &[
    Beat::new("the GPU itself", BEAT_MS)
        .note(
            "The logic die is the compute chip: the GPU or accelerator. It sits on an interposer with HBM stacks beside it.",
            "The package cut open with the lid off: two purple dies tiled with lilac blocks, gold HBM stacks at the sides, a grey interposer below.",
        )
        .detail("Everything else in the package serves this die.", &["Logic die = the GPU", "Leading-edge node"]),
    Beat::new("as big as one exposure", BEAT_MS)
        .note(
            "A scanner can only print a field 26 x 33 mm. Big AI dies are drawn right up to that limit.",
            "Looking down: a pink rectangle hugs the right-hand die with almost no margin.",
        )
        .detail("The field caps the die.", &["RETICLE LIMIT", "DIE SIZE ~ the field"]),
    Beat::new("more dies, joined", BEAT_MS)
        .note(
            "Past the limit, the only way to more silicon is more dies, joined by a fast link in the package, with HBM along their outer edges.",
            "Green beads cross the gap between the dies; cyan beads run out from the dies' edges to the HBM stacks.",
        )
        .detail("Chiplets plus a die-to-die link.", &["CHIPLETS", "DIE-TO-DIE", "HBM SHORELINE"]),
];

/// 2 the parts: the die cut open.
const S2_B: &[Beat] = &[
    Beat::new("the die cut open", BEAT_MS)
        .note(
            "Cut through a mounted die: microbumps and pads at the bottom, then the metal stack, then a thin transistor layer, then bulk silicon on top. It is mounted flip-chip, wiring side down.",
            "A tall cut block: copper pillars with solder caps at the bottom, a pale banded stack full of copper lines, a thin layer of grey fins and gold gate bars, and a thick purple slab above.",
        )
        .detail("Flip-chip: transistors face the bumps.", &["Bulk / transistors / metal / bumps", "~15 metal levels"]),
    Beat::new("the transistors", BEAT_MS)
        .note(
            "The transistor layer is a few hundred nanometres thick in life: rows of silicon fins crossed by gate lines. Signals climb to it from the bumps through the metal stack.",
            "Close on the thin layer: grey fins running into the block crossed by gold gate bars; cyan beads rise through the stack and stop at it.",
        )
        .detail("All the logic lives in one thin layer.", &["FinFET / GAA transistors", "N4/N3-class node"]),
    Beat::new("thick to thin", BEAT_MS)
        .note(
            "The metal levels near the bumps are thick and widely spaced, for power and long wires. Near the transistors they shrink to the finest pitch the node can print, for local wiring.",
            "The stack from the side: wide copper bars at the bottom levels grading to thin dense lines at the top; yellow beads climb a power column.",
        )
        .detail("Global levels carry power; local levels wire gates.", &["Global: thick", "Local: finest pitch"]),
];

/// 3 one die, in order.
const S3_B: &[Beat] = &[
    Beat::new("fields on a wafer", BEAT_MS)
        .note(
            "The design fills one reticle field. The wafer is exposed field by field and run through hundreds of process steps.",
            "A dark wafer seen from above, tiled with purple fields.",
        )
        .detail("Steps 1 and 2: design, expose.", &["1 one field", "2 field by field"]),
    Beat::new("wafer test", BEAT_MS)
        .note(
            "Probes test every die while it is still on the wafer. Dies hit by defects fail; the rest are marked good.",
            "Red dots across the wafer; the fields under them turn red, the others turn green.",
        )
        .detail("Step 3: find the good dies.", &["3 wafer test", "Good / bad map"]),
    Beat::new("a known-good die goes on", BEAT_MS)
        .note(
            "The wafer is cut up and only known-good dies go on. Each one is flipped and bonded onto the interposer beside its HBM.",
            "The package with its lid off: the right-hand die drops from above and settles onto the interposer next to its stacks.",
        )
        .detail("Steps 4 and 5: dice, test, bond.", &["4 KNOWN GOOD DIE", "5 bonded beside HBM"]),
];

/// 4 the reticle limit and die size.
const S4_B: &[Beat] = &[
    Beat::new("one field", BEAT_MS)
        .note(
            "The field is 26 mm across and 33 mm long: 858 mm2, set by the scanner's optics.",
            "A single pink-outlined field on the wafer, seen from above at an angle.",
        )
        .detail("The scanner's field.", &["26 x 33 mm", "858 mm2"]),
    Beat::new("the die fills it", BEAT_MS)
        .note(
            "NVIDIA's H100 is about 814 mm2, roughly 95% of the field. There is almost nothing left to grow into.",
            "The field filled edge to edge by a glowing violet die.",
        )
        .detail("Big AI dies are already at the limit.", &["H100 ~814 mm2", "~95% of the field"]),
    Beat::new("High-NA halves it", BEAT_MS)
        .note(
            "High-NA EUV prints a 26 x 16.5 mm field. The far half of today's big die would fall outside it, so single dies get smaller, not larger.",
            "Straight down on the field: a yellow outline round the near half, the far half of the die turned red.",
        )
        .detail("See the LITHO node.", &["High-NA: 26 x 16.5 mm", "Half the area"]),
];

/// 5 yield: why big dies cost more.
const S5_B: &[Beat] = &[
    Beat::new("defects land", BEAT_MS)
        .note(
            "Defects land at random. Their density is set by the fab, so every wafer gets a similar sprinkling.",
            "A wafer of purple fields with red dots appearing across it.",
        )
        .detail("Defects do not care about the design.", &["Random defects", "Fixed density"]),
    Beat::new("big dies lost", BEAT_MS)
        .note(
            "On an 800 mm2 die each defect scraps 800 mm2. Estimates put yield near 45-47% for dies this size at typical defect densities.",
            "Every field holding a red dot turns solid red; the tag counts the good ones.",
        )
        .detail("Yield falls fast with area.", &["YIELD ~45% at ~800 mm2 (est.)", "Cost per good die rises"]),
    Beat::new("chiplets lose less", BEAT_MS)
        .note(
            "Split the same area into smaller dies and the same defects scrap far less silicon. Testing each one first keeps bad dies out of expensive packages.",
            "The wafer tiled with four times as many small dies; only the few under red dots turn red.",
        )
        .detail("Smaller dies, tested first.", &["CHIPLETS", "KNOWN GOOD DIE"]),
];

/// 6 chiplets and the die-to-die link.
const S6_B: &[Beat] = &[
    Beat::new("the bridge", BEAT_MS)
        .note(
            "B200's two compute dies meet over silicon bridges sunk in the interposer, TSMC's CoWoS-L.",
            "A cut block: two purple dies over a gap, a teal bridge set into the grey interposer under it.",
        )
        .detail("CoWoS-L: bridges in the interposer.", &["CHIPLETS: 2 dies", "Silicon bridge"]),
    Beat::new("fine pitch", BEAT_MS)
        .note(
            "Over the bridge the bumps are packed tightly and the bridge's copper layers run straight across, so thousands of wires fit along the shared edge.",
            "Close: thin copper pillars over the bridge, fatter ones further out, copper lines inside the bridge.",
        )
        .detail("Wire count is what buys bandwidth.", &["Fine-pitch bumps", "Bridge wiring"]),
    Beat::new("about 10 TB/s", BEAT_MS)
        .note(
            "The link carries roughly 10 TB/s between the dies, wide and short enough that software sees a single GPU.",
            "Green beads cross the bridge in both directions.",
        )
        .detail("The link must look like on-die wiring.", &["DIE-TO-DIE ~10 TB/s", "One GPU"]),
];

/// 7 edges for memory, and heat.
const S7_B: &[Beat] = &[
    Beat::new("the shoreline", BEAT_MS)
        .note(
            "HBM stacks connect along the die's edge through the interposer, so the outer edges are the memory budget.",
            "Top view, lid off: yellow lines along both dies' outer edges, HBM stacks lined up beside them.",
        )
        .detail("More stacks need more edge.", &["HBM SHORELINE", "Outer edges only"]),
    Beat::new("data out", BEAT_MS)
        .note(
            "Data runs through the interposer's fine copper to each stack. Blackwell's memory bandwidth is about 8 TB/s, separate from the 10 TB/s die-to-die link.",
            "Close on the cut face: cyan beads run between the die edge and an HBM stack.",
        )
        .detail("Memory and die-to-die are different links.", &["~8 TB/s memory", "~10 TB/s die-to-die"]),
    Beat::new("heat", BEAT_MS)
        .note(
            "The logic die is the main heat source in the package. It is cooled from the top, through TIM and the lid.",
            "The dies glow orange under the lid; orange beads rise from its top.",
        )
        .detail("Cooling: see BOARD.", &["HEAT: the logic die", "Cooled from the top"]),
];

/// 8 who makes it.
const S8_B: &[Beat] = &[
    Beat::new("design and fab", BEAT_MS)
        .note(
            "NVIDIA and AMD design the dies; TSMC builds them on N4/N3-class nodes. Intel and Samsung build large logic dies in their own fabs.",
            "Top view with the dies lit violet.",
        )
        .detail("Fabless designers, one leading foundry.", &["NVDA, AMD design", "TSM builds"]),
    Beat::new("packaging and memory", BEAT_MS)
        .note(
            "TSMC also makes the interposer and bonds everything in CoWoS. The HBM comes from SK hynix, Samsung and Micron.",
            "The interposer's top lit with a violet sheen; HBM stacks at the sides.",
        )
        .detail("CoWoS capacity has been a bottleneck.", &["TSMC CoWoS", "SK hynix, Samsung, MU"]),
    Beat::new("substrate", BEAT_MS)
        .note(
            "Under it all, the substrate's build-up film comes from Ajinomoto and the substrates from makers such as Ibiden and Unimicron.",
            "Close on the cut face of the layered brown substrate and its copper lines.",
        )
        .detail("Small suppliers, big leverage.", &["ABF: Ajinomoto", "Ibiden, Unimicron"]),
];

/// 9 chokepoints and risks.
const S9_B: &[Beat] = &[
    Beat::new("the reticle cap", BEAT_MS)
        .note(
            "The reticle limit caps any single die. Growth has to come from more dies and bigger packages.",
            "Top view: a pink rectangle tight round one die.",
        )
        .detail("No bigger dies, only more of them.", &["RETICLE LIMIT", "More dies, bigger packages"]),
    Beat::new("one defect, one die", BEAT_MS)
        .note(
            "A single defect on a big die scraps the whole thing, which raises the cost of every good die.",
            "A red dot lands on the right-hand die, which then turns red.",
        )
        .detail("Large-die yield losses raise cost.", &["YIELD", "Cost per good die"]),
    Beat::new("every link to test", BEAT_MS)
        .note(
            "Every extra die adds a die-to-die link and a bridge that must be designed, built and tested, and that can fail.",
            "Close on the bridge: green beads crossing between the dies.",
        )
        .detail("Chiplets trade yield for complexity.", &["DIE-TO-DIE", "Bridge yield risk"]),
];
