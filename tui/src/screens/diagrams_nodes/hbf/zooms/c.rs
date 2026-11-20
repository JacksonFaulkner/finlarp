// R&D tab, HBF: zoom-in c, the UCIe link. The overview's package with the camera held on the inner
// HBF stack's base die, the interposer and the GPU's edge (tools/pbr3d/blender/rnd_hbf_zoom_c.py,
// GLB tools/pbr3d/assets/rnd_hbf_zoom_c.glb).

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_hbf_zoom_c.glb"),
        BEATS,
    )
}

/// Three beats (match rnd_hbf_zoom_c.py): reads reach the base die, cross the link, and the grades.
const BEATS: &[Beat] = &[
    Beat::new("reads reach the base die", BEAT_MS)
        .note(
            "Each NAND die's CMOS layer reads a page out of its array, and the data runs down the TSVs to the base die at the bottom of the stack. The base die is the part that talks to the GPU.",
            "One teal flash stack up close: bright beads run down its three copper TSVs into the blue base die beneath it, with the purple GPU to the left.",
        )
        .detail(
            "Every read leaves the stack through its base die.",
            &["TSVs: down through 16 dies", "Base die: the GPU side"],
        ),
    Beat::new("across the interposer", BEAT_MS)
        .note(
            "From the base die, data crosses the silicon interposer to the GPU. Trade press reports the link as UCIe, a chiplet link; the spec itself defines the xPU-HBF host interface between the processor and the stack.",
            "A low view of the interposer's cut face: cyan beads leave under the base die, run along a copper wire across the face and climb into the GPU.",
        )
        .detail(
            "The interposer carries HBF's data the same way it carries HBM's.",
            &["xPU-HBF host interface (spec)", "UCIe link (trade press)"],
        ),
    Beat::new("three bandwidth grades", BEAT_MS)
        .note(
            "The spec sets three bandwidth grades per stack, from about 0.4 TB/s up to 3.0 TB/s. SanDisk's first-generation target is 1.6 TB/s; 3.0 TB/s is the spec's ceiling, not a part that ships today.",
            "Three wires on the interposer light one after another, each carrying more beads than the last, from a sparse top lane to a dense bottom one.",
        )
        .detail(
            "The grades leave room for later generations.",
            &["0.4-3.0 TB/s grades (OCP spec)", "First-gen target 1.6 TB/s"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
