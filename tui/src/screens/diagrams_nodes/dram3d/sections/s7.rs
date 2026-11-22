// R&D tab, 3D DRAM: section 7 (heading 7 of diagrams_pages/RND_3D_DRAM.txt), "Stacked 3D DRAM:
// layers of sideways cells". Blender scene tools/pbr3d/blender/rnd_3d_dram_section_7.py, GLB
// tools/pbr3d/assets/rnd_3d_dram_section_7.glb. Three beats: Samsung's 16 layers on a bonded periphery,
// SK hynix's 5 layers and their yield, and how many layers it takes to pay.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_3d_dram_section_7.glb"),
        BEATS,
    )
}

/// The three beats (match rnd_3d_dram_section_7.py).
const BEATS: &[Beat] = &[
    Beat::new("sixteen layers on a bonded periphery", BEAT_MS)
        .note(
            "Stacked 3D DRAM turns the 1T1C cell on its side: a gate-all-around transistor and a horizontal capacitor per cell, horizontal word lines, and bit lines running vertically down through the layers. Samsung's VLSI 2026 paper (VS-DRAM) shows 16 layers built this way, with the periphery made on a separate wafer and bonded on.",
            "A grey periphery block with purple and green circuit blocks; cut-open layers of sideways cells drop onto it one after another until sixteen are stacked, each with long grey capacitors either side of a teal bit line. The bit line then glows cyan from top to bottom and beads run from a capacitor near the top, through its transistor and down the bit line into the periphery, whose sense-amp block lights.",
        )
        .detail(
            "One bit line serves a cell in every layer.",
            &["16 layers, GAA cells (VLSI 2026)", "Periphery on a bonded wafer (VLSI 2026)"],
        ),
    Beat::new("five layers, 56.1% yield", BEAT_MS)
        .note(
            "SK hynix showed a 5-layer stacked 3D DRAM at VLSI 2024 and reported a yield of 56.1%. That is a research figure for a few layers, far from what production needs.",
            "A shorter 5-layer block stands left of the 16-layer one. Its word lines light pink one layer at a time, bottom to top, counting the five layers; then all its capacitors light gold and a green bar in a white frame beside it fills a little past half way.",
        )
        .detail(
            "Five layers worked about half the time.",
            &["5 layers (SK hynix, VLSI 2024)", "56.1% yield (TrendForce)"],
        ),
    Beat::new("how many layers it takes", BEAT_MS)
        .note(
            "SK hynix said 32 to 192 layers are needed before stacked DRAM sees wide use. A Micron engineer estimated in 2021 that 200 to 300 layers are needed to beat planar DRAM on cost. Today's results are 5 and 16 layers.",
            "A bar chart on a white base, every bar in layers: two short teal bars for 5 and 16, then a tall gold bar from 32 to 192 standing on a thin grey post, and a gold block from 200 to 300 floating high above on its own post. Dark lines on the gold bars mark every 16 layers.",
        )
        .detail(
            "The demonstrations are a small fraction of what pays.",
            &["32-192 layers for wide use (SK hynix, TrendForce)", "200-300 to beat planar on cost (SemiEngineering, 2021)"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
