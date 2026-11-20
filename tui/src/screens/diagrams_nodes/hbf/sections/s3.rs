// R&D tab, HBF: section 3, "From flash cell to GPU, in order" (heading 3 of diagrams_pages/RND_HBF.txt),
// from tools/pbr3d/blender/rnd_hbf_section_3.py (GLB tools/pbr3d/assets/rnd_hbf_section_3.glb).

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_hbf_section_3.glb"),
        BEATS,
    )
}

/// Three beats: read a page, down the TSVs, into the GPU (match rnd_hbf_section_3.py).
const BEATS: &[Beat] = &[
    Beat::new("read a page", BEAT_MS)
        .note(
            "The model's weights sit in the NAND arrays of each die. To read them, the die's CMOS layer pulls a whole page out of its array, a far larger piece than a DRAM access.",
            "A close view of one flash stack's cut face: a page on one die's teal array layer lights up pale green, and small beads drop from it into the dark logic layer below and run to a copper TSV.",
        )
        .detail(
            "Flash reads in pages, not small words.",
            &["PAGE: larger than a DRAM access", "CMOS layer under the array"],
        ),
    Beat::new("down the TSVs", BEAT_MS)
        .note(
            "The data runs down the TSVs, the copper columns through every die, and crosses the microbumps between dies until it reaches the base die at the bottom of the stack.",
            "The whole flash stack: green beads run down its three copper columns past the yellow microbumps and gather in the blue base die.",
        )
        .detail(
            "Every die shares the same vertical wiring.",
            &["16 dies, one set of TSVs", "Base die at the bottom"],
        ),
    Beat::new("into the GPU", BEAT_MS)
        .note(
            "The base die sends the data over the UCIe link across the silicon interposer into the GPU. On the other side, the HBM stacks' reads arrive the same way, and the GPU uses both.",
            "The whole package: cyan beads leave the flash stacks' base dies, cross the grey interposer and reach the purple GPU, while yellow and cyan beads come in from the orange HBM stacks on the left; the GPU's top lights.",
        )
        .detail(
            "HBF adds capacity beside HBM, not instead of it.",
            &["UCIe link (trade press)", "HBM and HBF feed one GPU"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
