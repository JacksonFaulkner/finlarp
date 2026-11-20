// R&D tab, HBF: section 2, "The parts" (heading 2 of diagrams_pages/RND_HBF.txt). Blender scene
// tools/pbr3d/blender/rnd_hbf_section_2.py, GLB tools/pbr3d/assets/rnd_hbf_section_2.glb: the
// glossary shown piece by piece on a cut-open HBF stack beside the GPU.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_hbf_section_2.glb"),
        BEATS,
    )
}

/// The three beats (match rnd_hbf_section_2.py).
const BEATS: &[Beat] = &[
    Beat::new("a NAND die: array on logic", BEAT_MS)
        .note(
            "A NAND die is the memory array plus the CMOS logic that drives it. In CBA the logic is built on its own wafer and bonded directly under the array wafer.",
            "The top die of the stack hangs above it, split in two: a teal array layer with its strings on the cut face, and a dark logic layer below whose top lights up along the bond.",
        )
        .detail(
            "Two wafers make one die.",
            &["NAND DIE: array + logic", "CBA: CMOS bonded to array"],
        ),
    Beat::new("the stack and its link", BEAT_MS)
        .note(
            "A stack is 8 or 16 NAND dies on a base die, joined by TSVs and microbumps. The base die talks to the GPU over the xPU-HBF host interface, with UCIe as the chiplet link per trade press.",
            "The sixteen teal dies spread apart on a blue base die, copper TSVs running through them and yellow microbumps between; cyan beads cross the interposer from the base die to the purple GPU.",
        )
        .detail(
            "The base die is the stack's only door to the GPU.",
            &["STACK: 8 or 16 dies", "Link: xPU-HBF over UCIe"],
        ),
    Beat::new("pages, KV cache and wear", BEAT_MS)
        .note(
            "Flash reads in pages, much larger than a DRAM access. The KV cache, the model's working memory, is rewritten as it runs, and every rewrite wears the flash cells a little.",
            "A long glowing slab, one flash page, sits on top of the stack beside a tiny yellow block for a DRAM access, then both travel down to the GPU; cyan blocks drop into the stack while a gold meter beside it loses segments.",
        )
        .detail(
            "Flash suits data that is read far more than written.",
            &["PAGE: much larger than DRAM's", "ENDURANCE: rewrites wear cells"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
