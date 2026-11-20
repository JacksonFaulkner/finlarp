// R&D tab, HBF: section 6, "The spec" (heading 6 of diagrams_pages/RND_HBF.txt). Blender scene
// tools/pbr3d/blender/rnd_hbf_section_6.py -> tools/pbr3d/assets/rnd_hbf_section_6.glb: an 8-high
// and a 16-high HBF stack beside a GPU; the three bandwidth grades; the host interface.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_hbf_section_6.glb"),
        BEATS,
    )
}

const BEATS: &[Beat] = &[
    Beat::new("two stack sizes", BEAT_MS)
        .note(
            "The first OCP HBF specification, published on August 3, 2026, defines two stack configurations: 8 NAND dies high and 16 high. A stack holds up to 512 GB.",
            "Two teal flash stacks on a grey interposer, a short 8-high one on the left and a 16-high one twice its height on the right, with the purple GPU at the edge.",
        )
        .detail(
            "One spec, two heights.",
            &["8-high and 16-high", "Up to 512 GB a stack"],
        ),
    Beat::new("three bandwidth grades", BEAT_MS)
        .note(
            "The spec sets three bandwidth grades, from about 0.4 to 3.0 TB/s per stack. The top grade is the spec's ceiling, not a part that ships today.",
            "Three gold bars rise one after another at the left, short to tall, while green beads run down the 16-high stack.",
        )
        .detail(
            "A range for future generations to fill.",
            &["~0.4 to 3.0 TB/s", "3.0 TB/s: a ceiling"],
        ),
    Beat::new("the host interface", BEAT_MS)
        .note(
            "The spec defines the xPU-HBF host interface between a processor and the stack, with electrical guidelines, stack reliability and packaging, and a software guide for reads and writes. Trade press reports UCIe as the link. Google and Tenstorrent joined the workstream.",
            "The link strips at the side of each base die glow, and cyan beads cross the interposer from both stacks into the purple GPU.",
        )
        .detail(
            "A common interface, so any processor can attach HBF.",
            &["xPU-HBF host interface", "Google, Tenstorrent joined"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
