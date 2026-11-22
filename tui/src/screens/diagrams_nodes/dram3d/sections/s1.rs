// R&D tab, 3D DRAM: section 1 (heading 1 of diagrams_pages/RND_3D_DRAM.txt), "What it is: DRAM cells
// built upward". Blender scene tools/pbr3d/blender/rnd_3d_dram_section_1.py, GLB
// tools/pbr3d/assets/rnd_3d_dram_section_1.glb. Three beats: one flat planar cell, a VCT cell rising
// beside it (step one), and layers of sideways cells stacking up (step two).

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_3d_dram_section_1.glb"),
        BEATS,
    )
}

/// The three beats (match rnd_3d_dram_section_1.py).
const BEATS: &[Beat] = &[
    Beat::new("today's cell is built flat", BEAT_MS)
        .note(
            "A DRAM bit is one transistor and one capacitor. Today the transistor lies flat in the silicon and the capacitor stands on top of it, so every bit needs its own patch of floor: about 6F2, where F is the smallest feature.",
            "One planar cell cut open: a grey silicon block with maroon word lines in their trenches, a teal bit line on a contact, and a tall capacitor with a glowing gold rim. A gold-edged tile floats above it, and yellow beads run from the capacitor down into the bit line.",
        )
        .detail(
            "Each bit takes floor space.",
            &["6F2 = 2F x 3F (Bits&Chips)", "1T1C: one transistor, one capacitor"],
        ),
    Beat::new("step one: the transistor stands up", BEAT_MS)
        .note(
            "3D DRAM builds the cell upward instead. First the transistor stands up as a pillar, a vertical channel transistor (VCT), with the capacitor straight on top. That cell takes about 4F2. Samsung showed a 16 Gb chip built this way at ISSCC 2026.",
            "A second cell rises out of the floor beside the planar one: a tan pillar between maroon word-line bars, a teal bit line underneath and a capacitor on top. Its smaller green-edged tile floats over it, its word line glows pink and beads run down the pillar.",
        )
        .detail(
            "Less floor per bit.",
            &["4F2 = 2F x 2F (Bits&Chips)", "16 Gb VCT test chip (Samsung, ISSCC 2026)"],
        ),
    Beat::new("step two: stack the layers", BEAT_MS)
        .note(
            "Second, whole layers of cells are stacked, the way 3D NAND stacks flash. Each cell lies on its side and a bit line runs straight up through the layers. Samsung's slides put stacked DRAM in the early 2030s.",
            "On the right, layers drop in one after another: each a white slab carrying a sideways transistor and a long capacitor with a gold rim. A teal bit line runs up their left edge and glows cyan as beads run down it.",
        )
        .detail(
            "Then the cells go up in layers.",
            &["Stacked DRAM: early 2030s (Samsung roadmap)"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
