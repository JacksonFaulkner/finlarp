// R&D tab, HBF: zoom-in e, reads and writes. The overview's package held on the GPU with one HBM
// stack and one HBF stack (tools/pbr3d/blender/rnd_hbf_zoom_e.py, GLB
// tools/pbr3d/assets/rnd_hbf_zoom_e.glb): weights read from flash, the KV cache written mostly to
// HBM with a wear meter on the flash, and a scheduler that cuts flash writes.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_hbf_zoom_e.glb"),
        BEATS,
    )
}

/// The three beats (match rnd_hbf_zoom_e.py).
const BEATS: &[Beat] = &[
    Beat::new("weights: read, not written", BEAT_MS)
        .note(
            "The model's weights sit in the flash and are only read. Reads run down the stack to its base die and across the interposer into the GPU. Flash is slow to write and wears out as it is rewritten, so data that is read far more than written suits it.",
            "Green beads run down the TSVs of the teal flash stack to its base die, then cyan beads cross the interposer into the purple GPU, whose top lights up.",
        )
        .detail(
            "Weights are the read-mostly data HBF is built for.",
            &["Weights: read from HBF", "Read far more than written"],
        ),
    Beat::new("the KV cache: rewritten constantly", BEAT_MS)
        .note(
            "The KV cache, the model's working memory during a conversation, is rewritten as it runs. Most of those writes go to HBM; the ones that reach the flash wear it, and the wear meter over the stack climbs.",
            "Orange beads leave the GPU for both stacks, most to the orange HBM stack on the left, fewer to the teal flash stack; a row of orange segments over the flash fills one by one.",
        )
        .detail(
            "Write endurance limits what HBF can hold.",
            &["KV cache: rewritten constantly", "Flash wears with each write"],
        ),
    Beat::new("a scheduler that spares the flash", BEAT_MS)
        .note(
            "A UC Berkeley and FuriosaAI scheduler kept the KV cache in HBM and cut HBF KV writes by 94%, raising estimated write lifetime from 1.2 to 14.8 years. In another study, KV writes took 5-13.9% of run time.",
            "The writes to the flash all but stop and its wear meter falls back to two segments; above it a short gold bar for 1.2 years and a long teal bar for 14.8 years grow side by side.",
        )
        .detail(
            "Placement software decides how long the flash lasts.",
            &["94% fewer HBF KV writes", "1.2 > 14.8 years (est.)"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
