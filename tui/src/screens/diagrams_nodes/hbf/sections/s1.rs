// R&D tab, HBF: section 1 (heading 1 of diagrams_pages/RND_HBF.txt), "What it is: NAND flash in an
// HBM package". Blender scene tools/pbr3d/blender/rnd_hbf_section_1.py, GLB
// tools/pbr3d/assets/rnd_hbf_section_1.glb. Three beats: HBM beside the GPU, HBF stacked the same way
// on the same interposer, and the capacity it adds.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_hbf_section_1.glb"),
        BEATS,
    )
}

/// The three beats (match rnd_hbf_section_1.py).
const BEATS: &[Beat] = &[
    Beat::new("HBM: DRAM beside the GPU", BEAT_MS)
        .note(
            "Today a GPU's fast memory is HBM: DRAM dies stacked on top of each other and set beside the GPU on a silicon interposer, so the two can talk over thousands of short wires.",
            "A cut-open package: a purple GPU in the middle of a grey interposer, two orange DRAM stacks on each side of it, all on a green substrate.",
        )
        .detail(
            "HBM is fast but holds a limited amount.",
            &["HBM: stacked DRAM dies", "Beside the GPU, on the interposer"],
        ),
    Beat::new("HBF: NAND stacked the same way", BEAT_MS)
        .note(
            "HBF stacks NAND flash dies the way HBM stacks DRAM dies, and puts the stack beside the GPU on the same interposer. Here the two right-hand stacks become flash.",
            "The orange stacks on the right are gone; teal flash dies drop one by one onto blue base dies in their place until two 16-high stacks stand beside the GPU.",
        )
        .detail(
            "Same package, different memory.",
            &["HBF: high-bandwidth flash", "NAND in an HBM-style package"],
        ),
    Beat::new("far more capacity, less bandwidth", BEAT_MS)
        .note(
            "HBF gives an inference chip far more memory per GPU than HBM, at a bandwidth below HBM's. SanDisk and SK hynix lead the work, and the first open spec came out through the Open Compute Project in August 2026.",
            "Gold blocks rise over the stacks: one over each HBM stack, eight over each HBF stack. Small yellow beads run quickly down the HBM stacks while a few big green beads run later down the flash.",
        )
        .detail(
            "Capacity close to the GPU, for inference.",
            &["8-16x HBM's capacity (SanDisk)", "First OCP spec: Aug 2026"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
