// R&D tab, 3D DRAM: zoom-in d, "6F2 against 4F2" (tools/pbr3d/blender/rnd_3d_dram_zoom_d.py, GLB
// tools/pbr3d/assets/rnd_3d_dram_zoom_d.glb). A planar cell beside a VCT cell with their F-grid tiles, a
// 6F x 6F patch tiled both ways, then two wafers.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_3d_dram_zoom_d.glb"),
        BEATS,
    )
}

const BEATS: &[Beat] = &[
    Beat::new("2F x 3F against 2F x 2F", BEAT_MS)
        .note(
            "Cell area is counted in squares of F, the smallest feature. Today's planar cell needs 2F x 3F because its transistor lies flat beside the capacitor contact. Standing the transistor up under the capacitor leaves 2F x 2F.",
            "Two cells cut open side by side: on the left a planar cell with its transistor in a block of silicon and a gold-tiled 3 x 2 grid overhead; on the right a VCT pillar under its capacitor with a green 2 x 2 tile overhead.",
        )
        .detail(
            "Same F, a third less area per cell.",
            &["6F2 = 2F x 3F", "4F2 = 2F x 2F [5]"],
        ),
    Beat::new("9 cells where 6 fit", BEAT_MS)
        .note(
            "Lay both kinds on the same 6F x 6F patch. Planar 2F x 3F tiles fit six; 2F x 2F tiles fit nine. That is the 50% more cells at the same F; The Elec puts the real gain at 30 to 50% more density per die.",
            "Two square F-grids seen from above, gold-rimmed on the left and green on the right. Tiles drop in one by one, each with a capacitor top: six long tiles on the left, nine square ones on the right.",
        )
        .detail(
            "Density without a smaller F.",
            &["~50% more cells at the same F [5]", "30-50% more density per die (The Elec) [2]"],
        ),
    Beat::new("more dies on every wafer", BEAT_MS)
        .note(
            "Smaller cells plus the periphery moved under the array make a smaller die, so more fit on a wafer. Samsung says its 4F2 cell-on-peripheral test chip gets over 20% more dies per wafer under the same design rules. Extra steps and new materials can still eat into the cost gain.",
            "Two wafers side by side, the right one tiled with visibly smaller, more numerous teal dies (drawn about 29% more).",
        )
        .detail(
            "Smaller cells only pay if the extra steps don't cost more [5].",
            &[">20% more dies per wafer (Samsung) [1]", "same design rules [1]"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
