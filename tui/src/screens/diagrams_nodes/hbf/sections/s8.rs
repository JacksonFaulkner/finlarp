// R&D tab, HBF: section 8, the weak spot: writes (heading 8 of diagrams_pages/RND_HBF.txt). Blender
// scene tools/pbr3d/blender/rnd_hbf_section_8.py, GLB tools/pbr3d/assets/rnd_hbf_section_8.glb.
// Three beats: weights are read, not written; the KV cache wears the flash; a scheduler moves the
// writes off it.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_hbf_section_8.glb"),
        BEATS,
    )
}

const BEATS: &[Beat] = &[
    Beat::new("read far more than written", BEAT_MS)
        .note(
            "Flash wears out as it is rewritten, and it is slow to write. Model weights are written once and then read again and again, which suits HBF.",
            "Green beads stream down a teal flash stack and across to the purple GPU; a single red bead goes the other way. A short red bar sits in the dark wear meter beside the stack.",
        )
        .detail(
            "Flash suits data that is read far more than written.",
            &["Weights: read, rarely written", "Writes are slow and wear cells"],
        ),
    Beat::new("the KV cache wears the flash", BEAT_MS)
        .note(
            "The KV cache, the model's working memory during a conversation, is rewritten constantly. In one study, KV writes took 5-13.9% of run time.",
            "A stream of red beads leaves the GPU and climbs into the flash stack, one after another, while the red fill in the wear meter climbs toward the top.",
        )
        .detail(
            "Constant rewrites are what flash handles worst.",
            &["KV writes: 5-13.9% of run time", "arXiv 2608.13868"],
        ),
    Beat::new("move the writes off the flash", BEAT_MS)
        .note(
            "A scheduler from UC Berkeley and FuriosaAI cut HBF KV writes by 94%. That raised the estimated write lifetime from 1.2 to 14.8 years.",
            "The red beads now head left into the orange HBM stack; hardly any reach the flash. The wear meter falls, and two gold bars rise beside it, one short and one tall.",
        )
        .detail(
            "Placing the writes well makes the flash last.",
            &["94% fewer HBF KV writes", "Lifetime 1.2 > 14.8 years (est.)"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
