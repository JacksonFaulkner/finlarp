// R&D tab, 3D DRAM: section 6 (heading 6 of diagrams_pages/RND_3D_DRAM.txt), "Wafer-to-wafer
// bonding: periphery under the array". Blender scene tools/pbr3d/blender/rnd_3d_dram_section_6.py, GLB
// tools/pbr3d/assets/rnd_3d_dram_section_6.glb. Three beats: two wafers made with two processes, one
// die's periphery moving under its array, and the dies-per-wafer gain.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_3d_dram_section_6.glb"),
        BEATS,
    )
}

/// The three beats (match rnd_3d_dram_section_6.py).
const BEATS: &[Beat] = &[
    Beat::new("two wafers, two processes", BEAT_MS)
        .note(
            "Samsung's ISSCC 2026 test chip, 16 Gb and 10 nm class, builds its 4F2 VCT cells on one wafer and the periphery (sense amps, decoders, wiring) on another wafer made with a logic process. Each half ends in a face of copper pads, and the two wafers are joined by wafer-to-wafer hybrid copper bonding.",
            "Two wafers lie side by side, teal dies on the left and purple dies on the right. A cut-open chunk grows up out of each on a thin stem: on the left a row of VCT cells with tall capacitors over a strip of copper pads, on the right a block of logic transistors and copper wiring under a white pad layer. The capacitors light gold, a word line glows pink, a bit line cyan, beads run down a pillar, and the purple and green blocks in the periphery chunk light up.",
        )
        .detail(
            "Cells and logic each get the process that suits them.",
            &["16 Gb, 10 nm class, 4F2 VCT (ISSCC 2026)", "Periphery wafer: logic process (TrendForce)"],
        ),
    Beat::new("the periphery moves under the array", BEAT_MS)
        .note(
            "On a flat DRAM die the periphery sits beside the cell array and takes floor space of its own. Bonded underneath, it shares the array's footprint, so the same design rules give a smaller die. Samsung calls this cell-on-peripheral; SK hynix plans the same split, with circuits bonded below the cell area.",
            "A teal die block with a grey strip of purple and green circuit blocks along its right side, inside a gold outline. The array lifts, the strip drops, spreads flat and slides under it, the array settles back down onto it with a pale glowing seam, and the gold outline shrinks to the array's edge. Beads drop from the array into the layer below.",
        )
        .detail(
            "Same cells, less die area.",
            &["Cell-on-peripheral (ISSCC 2026)", "SK hynix: circuits under cells (VLSI 2025)"],
        ),
    Beat::new("more dies per wafer", BEAT_MS)
        .note(
            "A smaller die means more of them fit on each wafer. Samsung says cell-on-peripheral gives over 20% more dies per wafer under the same design rules. The test chip reads and writes; it is a research result, not a product.",
            "Seen from above, two wafers: on the left, dies each carrying a purple periphery band; on the right, a bonded pair with a glowing rim and a denser grid of smaller teal dies. A bright bar sweeps across each wafer, counting.",
        )
        .detail(
            "The gain is in wafer count, not in the cell itself.",
            &[">20% more dies per wafer (Samsung, ISSCC 2026)", "Test chip reads and writes (ISSCC 2026)"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
