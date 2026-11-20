// R&D tab, HBF: section 9, who is building it, timing and risks (heading 9 of
// diagrams_pages/RND_HBF.txt). Blender scene tools/pbr3d/blender/rnd_hbf_section_9.py, GLB
// tools/pbr3d/assets/rnd_hbf_section_9.glb.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_hbf_section_9.glb"),
        BEATS,
    )
}

/// who; timing; risks (match rnd_hbf_section_9.py's beats).
const BEATS: &[Beat] = &[
    Beat::new("who is building it", BEAT_MS)
        .note(
            "SanDisk and SK hynix wrote the HBF spec. Samsung has filed a \"zHBF\" trademark and is reported to be in early design. Kioxia's high-bandwidth flash is a PCIe module, not a stack in the GPU's package.",
            "Two teal flash stacks beside the purple GPU, tagged SanDisk and SK hynix; a grey see-through stack on the GPU's other side for Samsung; a green add-in card standing in a slot off the package for Kioxia.",
        )
        .detail(
            "Two makers wrote the spec; others are circling.",
            &["SanDisk (SNDK), SK hynix", "Samsung: zHBF trademark"],
        ),
    Beat::new("from MOU to samples", BEAT_MS)
        .note(
            "SanDisk and SK hynix signed an MOU in February 2026 and released the first OCP spec in August. SanDisk targets HBF memory samples in the second half of 2026 and samples of the first inference devices in early 2027.",
            "Four things appear in turn along a grey plinth, left to right: a signed sheet, a stack of spec pages with a gold band, a single teal flash stack, and a small GPU with flash stacks beside it.",
        )
        .detail(
            "A roadmap, not a shipping product.",
            &["Samples H2 2026", "Inference devices early 2027"],
        ),
    Beat::new("the risks", BEAT_MS)
        .note(
            "No HBF product is on sale, and the performance figures are company claims or simulations. Write endurance limits what the flash can hold, and a shared interface does not guarantee that parts from different vendors are interchangeable.",
            "Back on the package: hot dots rain onto the outer flash stack while a glowing gauge beside it drains from full to a quarter; cyan beads still cross into the GPU.",
        )
        .detail(
            "The open questions are endurance and adoption.",
            &["Nothing on sale yet", "Writes wear the flash"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
