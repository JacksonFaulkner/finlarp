// R&D tab, 3D DRAM: section 4 (heading 4 of diagrams_pages/RND_3D_DRAM.txt), "Why DRAM has to go
// vertical". Blender scene tools/pbr3d/blender/rnd_3d_dram_section_4.py, GLB
// tools/pbr3d/assets/rnd_3d_dram_section_4.glb. Three beats: capacitors growing taller as they narrow,
// the tallest one leaning over and shorting, and equal floor plates holding 8 cells at 6F2 against 12
// at 4F2.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_3d_dram_section_4.glb"),
        BEATS,
    )
}

/// The three beats (match rnd_3d_dram_section_4.py).
const BEATS: &[Beat] = &[
    Beat::new("narrower means taller", BEAT_MS)
        .note(
            "A DRAM cell keeps its bit in a tall, narrow capacitor. When the cell shrinks, the capacitor's radius shrinks too, so it has to grow taller to keep the same charge.",
            "Four capacitors cut open on a grey strip grow up one after another, left to right: each thinner than the last and taller, the fourth a thin needle. Each fills with a gold glow as it finishes.",
        )
        .detail(
            "Same charge, thinner and taller every shrink.",
            &["10a node est. 9.5-9.7 nm (TrendForce)"],
        ),
    Beat::new("tall capacitors yield poorly", BEAT_MS)
        .note(
            "Tall, thin capacitors are hard to make with good yield. One way they fail: a capacitor this slender can lean over and touch its neighbour, shorting both cells.",
            "Close and from above: the tallest needle tips over to the left until its side meets the top of its neighbour, and a red spark flashes where they touch.",
        )
        .detail(
            "The capacitor stops the flat cell from shrinking.",
            &["Tall capacitors yield poorly (SemiEngineering)"],
        ),
    Beat::new("the way out: less floor per cell", BEAT_MS)
        .note(
            "So the cell has to use less floor instead. Today's cells take about 6F2 (2F x 3F). A 4F2 cell (2F x 2F) is a third smaller, which fits about 50% more cells at the same F; The Elec estimates 30-50% more density per die.",
            "Two equal floor plates seen from above, 12F by 4F each. Gold-edged 6F2 tiles fill the back plate, eight of them; green-edged 4F2 tiles fill the front plate, twelve of them, each with a capacitor stub.",
        )
        .detail(
            "Same floor, half as many cells again.",
            &["4F2: ~50% more cells at the same F (Bits&Chips)", "30-50% more density per die (The Elec)"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
