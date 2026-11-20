// R&D tab, HBF: zoom-in a, "the stack cut open" (tools/pbr3d/blender/rnd_hbf_zoom_a.py, GLB
// tools/pbr3d/assets/rnd_hbf_zoom_a.glb). One 16-high HBF stack: whole, spread apart, then beside an
// 8-high HBM stack.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_hbf_zoom_a.glb"),
        BEATS,
    )
}

const BEATS: &[Beat] = &[
    Beat::new("16 NAND dies on a base die", BEAT_MS)
        .note(
            "An HBF stack is 16 NAND flash dies piled on a base die. Copper TSVs run down through every die, and the base die's UCIe strip faces the GPU.",
            "One teal stack cut open at its front face: sixteen thin dies on a blue base die, three brown copper columns running top to bottom, a gold strip on the base die's left edge.",
        )
        .detail(
            "The base die is the stack's only link to the processor.",
            &["16 NAND dies", "TSVs through every die"],
        ),
    Beat::new("16 x 256 Gb = 512 GB", BEAT_MS)
        .note(
            "Pulled apart, the dies show the microbumps that join each one to the die below. SanDisk's first-generation target is 256 Gb a die, so sixteen of them make 512 GB in one stack.",
            "The dies rise apart, the top ones furthest, with rows of yellow microbumps glowing in the gaps, then settle back together.",
        )
        .detail(
            "Capacity comes from stacking many dense dies.",
            &["256 Gb a die (first-gen target)", "512 GB a stack"],
        ),
    Beat::new("about as tall as HBM", BEAT_MS)
        .note(
            "Beside an 8-high HBM stack, the 16-high HBF stack comes out about the same height. SanDisk says HBF's footprint, stack height and power are close to HBM4's, so it fits the same place in the package.",
            "An orange 8-high DRAM stack appears on the left; a pale pink line runs across the tops of both stacks at the same height.",
        )
        .detail(
            "Same footprint and height, far more bits (SanDisk's claim).",
            &["Height close to HBM4", "HBM 8 dies, HBF 16"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
