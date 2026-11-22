// R&D tab, 3D DRAM: the page's overview, a Blender scene (tools/pbr3d/blender/rnd_3d_dram_overview.py,
// GLB tools/pbr3d/assets/rnd_3d_dram_overview.glb). Seven beats: today's planar 6F2 cell, why
// shrinking it stalls, the 4F2 vertical channel transistor, the periphery bonded under the array,
// stacked layers of sideways cells, the floating-body problem, and the reported road ahead.

use super::super::blender::{BEAT_MS, Cell, Page};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/rnd_3d_dram_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview, one per step (match rnd_3d_dram_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("today's DRAM cell lies flat", BEAT_MS)
        .note(
            "Each bit is one transistor and one capacitor (1T1C). The transistor lies flat in the silicon, its word line buried in a trench, and a tall capacitor stands on top holding the bit as charge. The cell takes about 6F2: 2F by 3F, where F is the smallest feature.",
            "Six cells cut open: a grey silicon block with maroon word lines in their trenches and teal bit lines on contacts above, three tall capacitors with glowing gold rims, and a gold-edged tile floating above the middle cell. A row lights and yellow beads run from a capacitor down into the bit line.",
        )
        .detail(
            "Almost all of a planar cell's height is its capacitor.",
            &["6F2 = 2F x 3F (Bits&Chips)", "1T1C: one transistor, one capacitor"],
        ),
    Beat::new("shrinking stalls", BEAT_MS)
        .note(
            "To make the cell smaller the capacitor has to get narrower, and a narrower capacitor must grow taller to keep enough charge. Tall, thin capacitors are hard to make with good yield, so the old way of shrinking is running out.",
            "The three capacitors squeeze thinner and stretch upward until they poke through a red line drawn above the row.",
        )
        .detail(
            "The capacitor sets how small a flat cell can get.",
            &["Tall capacitors yield poorly (SemiEngineering)", "10a node est. 9.5-9.7 nm (TrendForce)"],
        ),
    Beat::new("stand the transistor up", BEAT_MS)
        .note(
            "A vertical channel transistor (VCT) puts source, channel and drain in one upright silicon pillar. The word line wraps the pillar as its gate, the bit line is buried underneath, and the capacitor sits straight on top. The cell shrinks to 4F2, 2F by 2F: a third smaller.",
            "A 4 by 4 grid of cells: tan pillars edged in yellow gate oxide, maroon word lines on both sides of each pillar, teal bit lines underneath, a capacitor on every pillar. One word line glows pink, a bit line glows cyan, and a pale green-edged tile floats on top.",
        )
        .detail(
            "The transistor now takes no more floor than the capacitor above it.",
            &["4F2: ~50% more cells at the same F (Bits&Chips)", "30-50% more density per die (The Elec)"],
        ),
    Beat::new("periphery on its own wafer", BEAT_MS)
        .note(
            "The sense amps and decoders that run the array are built on a second wafer with a logic process. The cell wafer is bonded on top, copper pad to copper pad (cell on periphery). Samsung's 16 Gb ISSCC 2026 test chip was built this way and says it gets over 20% more dies per wafer.",
            "The cell array drops onto a grey periphery block whose white top carries copper pads. A pale line glows along the joint, beads drop through the pads, and the purple sense-amp and green decoder blocks inside light up.",
        )
        .detail(
            "Moving the periphery underneath frees floor space for cells.",
            &["16 Gb, 10 nm-class, W2W Cu bond (ISSCC 2026)", ">20% more dies per wafer (Samsung)"],
        ),
    Beat::new("stack the cells in layers", BEAT_MS)
        .note(
            "Stacked 3D DRAM lays each 1T1C cell on its side: a gate-all-around transistor and a capacitor lying flat, with horizontal word lines and bit lines running vertically through the layers. Samsung's VLSI 2026 paper shows 16 layers built this way.",
            "Eight layers of cells, gold-rimmed capacitors pointing out to both sides of a teal column, pull apart and close again. The column lights cyan, one layer's word lines glow pink, and beads run from a capacitor into the column.",
        )
        .detail(
            "Stacking is how DRAM would follow 3D NAND.",
            &["VS-DRAM: 16 layers (Samsung, VLSI 2026)", "SK hynix: 5 layers, 56.1% yield (2024)", "32-192 layers needed (SK hynix)"],
        ),
    Beat::new("the floating body", BEAT_MS)
        .note(
            "A vertical pillar is cut off from the silicon below, so its body has nowhere to drain stray charge. Holes build up in it and lower the transistor's threshold voltage, so it turns on early and leaks. Fixes include a back gate (SK hynix) and an IGZO oxide channel (Kioxia and Nanya).",
            "Close on one cut-open pillar: pink dots appear one by one inside its body until it glows pink, while on the plot beside it the bright cyan curve slides left of the grey one.",
        )
        .detail(
            "The vertical transistor's main weakness.",
            &["SK hynix VG: back gate sets Vt (VLSI 2026)", "IGZO: leakage < 1 aA (Kioxia, IEDM 2024)"],
        ),
    Beat::new("targets, not products", BEAT_MS)
        .note(
            "Samsung showed its 16 Gb VCT chip at ISSCC 2026, and press reports say it has working 10a dies and targets mass production in 2028. Stacked 3D DRAM is on its roadmap for the early 2030s. Micron skips 4F2, saying the capacitor pitch defines the DRAM.",
            "All three side by side: the planar cells, the VCT array on its glowing bond line and the stacked block, each lit and reading, with a date tag appearing over each.",
        )
        .detail(
            "Dates are company targets or press reports; nothing is on sale yet.",
            &["4F2 mass production: 2028 target (TrendForce)", "Stacked: early 2030s (Samsung roadmap)"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn beat_count_matches_the_script() {
        assert_eq!(super::BEATS.len(), 7);
    }
}
