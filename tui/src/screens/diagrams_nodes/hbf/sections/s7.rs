// R&D tab, HBF: section 7, "What the papers found" (heading 7 of diagrams_pages/RND_HBF.txt), from
// tools/pbr3d/blender/rnd_hbf_section_7.py (GLB tools/pbr3d/assets/rnd_hbf_section_7.glb). Three
// beats: FlashAccel's six stacks, Son et al.'s read-bandwidth point, and the three-tier hierarchy.
// All three results are simulations.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_hbf_section_7.glb"),
        BEATS,
    )
}

const BEATS: &[Beat] = &[
    Beat::new("FlashAccel: six stacks", BEAT_MS)
        .note(
            "FlashAccel added six HBF stacks to an HBM GPU. In simulation it got about 2.49x the throughput per GPU and 1.93x the energy efficiency, under a 100 ms latency limit.",
            "The package seen from above: two orange HBM stacks, six teal HBF stacks in two rows, and over the GPU a short grey bar beside a gold bar about two and a half times as tall.",
        )
        .detail(
            "Capacity beside the GPU raised throughput, in simulation.",
            &["~2.49x throughput per GPU", "1.93x energy efficiency"],
        ),
    Beat::new("capacity is not enough", BEAT_MS)
        .note(
            "Son et al. found that capacity alone is not enough: HBF also needs read bandwidth close to HBM's. A big store that reads slowly still leaves the GPU waiting.",
            "A wide translucent pipe runs from a flash stack under a gold pile to the GPU, carrying a few slow beads; then a thin copper pipe appears beside it, carrying many quick yellow beads.",
        )
        .detail(
            "Read bandwidth sets the pace, not size.",
            &["Son et al. (arXiv 2608.13868)", "Needs reads near HBM speed"],
        ),
    Beat::new("three tiers", BEAT_MS)
        .note(
            "UC Berkeley and FuriosaAI tested HBM, HBF and host memory as three tiers. Workloads finished 46-60% sooner than with HBM alone. FLINT similarly keeps HBF as a read-mostly tier beside HBM.",
            "The whole package with blue host memory sticks off to its right; beads run from host memory into the flash and from every stack into the GPU, while a gold bar ends about halfway along a grey one above.",
        )
        .detail(
            "Each tier holds what suits its speed.",
            &["46-60% less completion time", "HBM, HBF, host memory"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
        assert_eq!(super::build().beats().len(), 3);
    }
}
