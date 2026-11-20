// R&D tab, HBF: section 4, why inference wants capacity (heading 4 of diagrams_pages/RND_HBF.txt).
// Blender scene tools/pbr3d/blender/rnd_hbf_section_4.py -> tools/pbr3d/assets/rnd_hbf_section_4.glb.
// Three beats: weights sit beside the GPU; 810 GB fills a plinth of HBM stacks; two HBF stacks hold it.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_hbf_section_4.glb"),
        BEATS,
    )
}

const BEATS: &[Beat] = &[
    Beat::new("weights beside the GPU", BEAT_MS)
        .note(
            "To run a model, the GPU reads its weights from memory that sits right beside it on the package. The weights have to fit in that memory.",
            "A purple GPU on a grey interposer with two orange HBM stacks at its left; a gold block of weights sits on each stack, and cyan beads run from the stacks into the GPU.",
        )
        .detail(
            "Capacity beside the GPU sets which models fit.",
            &["Weights live in memory near the GPU"],
        ),
    Beat::new("810 GB of weights", BEAT_MS)
        .note(
            "Llama 3.1 405B at 16 bits per weight is about 810 GB. Held in HBM, that takes many stacks: the plinth fills with them, two rows deep, each taking its share of the weights.",
            "Looking down on a wide plinth: orange HBM stacks in two rows on both sides of the GPU, a gold block landing on each stack one after another.",
        )
        .detail(
            "Large models need many HBM stacks.",
            &["Llama 3.1 405B: ~810 GB at 16 bits"],
        ),
    Beat::new("two stacks of flash", BEAT_MS)
        .note(
            "SanDisk claims HBF holds 8-16x the capacity of HBM at a similar cost. At 512 GB a stack, two HBF stacks hold the same 810 GB that took the whole row of HBM.",
            "The HBM rows are gone but for one stack; two teal HBF stacks stand at the GPU's right with a large gold block on each, and cyan beads cross into the GPU.",
        )
        .detail(
            "Same weights, far fewer stacks.",
            &["8-16x HBM's capacity (SanDisk)", "512 GB a stack: two hold 810 GB"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
