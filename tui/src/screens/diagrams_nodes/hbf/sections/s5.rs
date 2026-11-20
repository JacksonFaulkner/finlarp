// R&D tab, HBF: section 5, "Inside the stack" (heading 5 of diagrams_pages/RND_HBF.txt), from
// tools/pbr3d/blender/rnd_hbf_section_5.py (GLB tools/pbr3d/assets/rnd_hbf_section_5.glb).

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_hbf_section_5.glb"),
        BEATS,
    )
}

/// 5 inside the stack: 16 dies, 512 GB; logic bonded under the array; as tall as HBM.
const BEATS: &[Beat] = &[
    Beat::new("16 dies, 512 GB", BEAT_MS)
        .note(
            "SanDisk's first-generation target stacks 16 NAND dies of 256 Gb each on a base die: 512 GB in one stack. TSVs and microbumps join the dies.",
            "One teal stack on a grey interposer, its dies pulling slightly apart so all sixteen can be counted, copper TSVs through them and yellow microbumps between, on a blue base die.",
        )
        .detail(
            "Sixteen dies of flash make one stack.",
            &["16 x 256 Gb = 512 GB", "SanDisk target, July 2025"],
        ),
    Beat::new("logic under the array", BEAT_MS)
        .note(
            "Each die is two layers: the CMOS logic that drives the flash, and the NAND array. In SanDisk's CBA the logic is built on its own wafer and bonded directly under the array.",
            "The top die rises off the stack; its teal array layer lifts away from a dark logic layer below, then drops back and a pale line glows along the bond.",
        )
        .detail(
            "Two wafers bonded into one die.",
            &["CBA: CMOS bonded to array"],
        ),
    Beat::new("about as tall as HBM", BEAT_MS)
        .note(
            "An 8-high HBM stack stands beside the 16-high HBF stack at the same height. SanDisk says HBF's footprint, stack height and power are close to HBM4's; its first-generation read target is 1.6 TB/s.",
            "An orange DRAM stack on the left and the teal flash stack on the right, a thin pink line across both tops; green beads run down the flash stack's TSVs.",
        )
        .detail(
            "Company figures, not measured parts.",
            &["Height close to HBM4 (SanDisk)", "1.6 TB/s read target"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
