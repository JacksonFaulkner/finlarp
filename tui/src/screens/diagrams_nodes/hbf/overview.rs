// R&D tab, HBF: the page's overview, a Blender scene (tools/pbr3d/blender/rnd_hbf_overview.py, GLB
// tools/pbr3d/assets/rnd_hbf_overview.glb). Seven beats: a GPU with HBM on one side and HBF on the
// other, the 16-die flash stack, CBA bonding, weights streaming into the GPU, capacity against
// speed, the six-stack result from the papers, and the road from spec to samples.

use super::super::blender::{BEAT_MS, Cell, Page};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/rnd_hbf_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview, one per step (match rnd_hbf_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("a GPU with flash beside it", BEAT_MS)
        .note(
            "A GPU sits on a silicon interposer with two kinds of memory stack beside it. On the left are HBM stacks of DRAM; on the right are HBF stacks of NAND flash, packaged the same way.",
            "A cut-open package: a purple GPU in the middle of a grey interposer on a green substrate, two orange DRAM stacks on its left and two teal flash stacks on its right.",
        )
        .detail(
            "HBF puts flash where HBM sits.",
            &["HBF: NAND in an HBM-style package", "SanDisk with SK hynix"],
        ),
    Beat::new("16 NAND dies, one stack", BEAT_MS)
        .note(
            "An HBF stack is 16 NAND dies on a base die, joined by TSVs and microbumps. SanDisk's first-generation target is 256 Gb a die, which makes 512 GB a stack, in a stack about as tall as HBM.",
            "One teal stack up close, its dies pulling slightly apart so all sixteen can be counted, copper TSVs running through them and yellow microbumps between, on a blue base die.",
        )
        .detail(
            "Flash packs far more bits into the same stack.",
            &["16 x 256 Gb = 512 GB", "Height close to HBM4"],
        ),
    Beat::new("logic under the array", BEAT_MS)
        .note(
            "Each NAND die is two wafers bonded together: the CMOS logic that drives the flash, and the memory array on top. SanDisk calls this CBA, CMOS directly bonded to array.",
            "The top die lifts off the stack and splits: the teal array layer rises off a dark logic layer, then drops back, and a pale line glows along the bond.",
        )
        .detail(
            "Building the logic on its own wafer frees the array's area.",
            &["CBA: CMOS bonded to array", "Two wafers, one die"],
        ),
    Beat::new("weights stream up", BEAT_MS)
        .note(
            "The model's weights sit in the flash. Reads run down each stack to its base die and cross the interposer over the UCIe link into the GPU. The spec sets three grades from about 0.4 to 3.0 TB/s per stack.",
            "Green beads run down the TSVs of both flash stacks to their base dies, then cyan beads cross the interposer into the GPU, whose top lights up.",
        )
        .detail(
            "Weights are read far more than written, which suits flash.",
            &["0.4-3.0 TB/s grades (OCP spec)", "First-gen target 1.6 TB/s"],
        ),
    Beat::new("capacity against speed", BEAT_MS)
        .note(
            "HBM answers quickly in small pieces. HBF holds 8 to 16 times as much at a similar cost, but answers later and in bigger pages. SanDisk's simulation put Llama 3.1 405B on HBF within 2.2% of an unlimited HBM.",
            "Above the left HBM stack, one gold block; above the right HBF stack, eight. Small yellow beads stream quickly down the HBM stack, while a few large green beads start late down the HBF stack.",
        )
        .detail(
            "Flash trades latency for capacity.",
            &["8-16x HBM's capacity (SanDisk)", "Higher latency, larger pages"],
        ),
    Beat::new("what the papers measured", BEAT_MS)
        .note(
            "Researchers have simulated HBF beside HBM. FlashAccel added six HBF stacks to an HBM GPU and got about 2.49x the throughput per GPU and 1.93x the energy efficiency, under a 100 ms latency limit.",
            "The camera rises to look down on the package: four more teal stacks stand in a back row, six in all, beside the orange HBM, and the GPU's top glows as data flows in.",
        )
        .detail(
            "A simulation, not a measured part.",
            &["2.49x throughput (FlashAccel)", "1.93x energy efficiency"],
        ),
    Beat::new("from spec to samples", BEAT_MS)
        .note(
            "SanDisk and SK hynix signed an MOU in February 2026 and released the first OCP spec in August. SanDisk targets HBF samples in the second half of 2026 and the first inference devices in early 2027.",
            "The whole package running at once, every stack sending data to the GPU, while four dates appear one after another above it.",
        )
        .detail(
            "A spec and a roadmap: nothing is on sale yet.",
            &["Aug 2026: first OCP spec", "Samples H2 2026, devices 2027"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn beat_count_matches_the_script() {
        assert_eq!(super::BEATS.len(), 7);
    }
}
