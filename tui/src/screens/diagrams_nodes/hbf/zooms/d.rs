// R&D tab, HBF: zoom-in d, HBM against HBF. An 8-high HBM stack and a 16-high HBF stack side by
// side (tools/pbr3d/blender/rnd_hbf_zoom_d.py, GLB tools/pbr3d/assets/rnd_hbf_zoom_d.glb): capacity,
// speed, and SanDisk's Llama 3.1 405B simulation.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_hbf_zoom_d.glb"),
        BEATS,
    )
}

/// The three beats (match rnd_hbf_zoom_d.py).
const BEATS: &[Beat] = &[
    Beat::new("capacity", BEAT_MS)
        .note(
            "An HBM stack of DRAM and an HBF stack of NAND flash stand side by side, the same height. SanDisk claims the flash stack holds 8 to 16 times as much at a similar cost.",
            "An orange DRAM stack on the left and a teal flash stack on the right, on a grey slab; one gold block floats over the DRAM stack and eight appear over the flash stack.",
        )
        .detail(
            "Flash stores far more bits in the same stack.",
            &["8-16x HBM's capacity (SanDisk)", "Similar cost"],
        ),
    Beat::new("speed", BEAT_MS)
        .note(
            "HBM answers quickly, in small pieces. HBF answers later and reads in bigger pages, so its latency is higher even when its bandwidth is close.",
            "Small yellow beads stream quickly down the DRAM stack's TSVs; a few large green beads start late down the flash stack's.",
        )
        .detail(
            "Flash trades latency for capacity.",
            &["Higher latency", "Larger pages"],
        ),
    Beat::new("405B within 2.2%", BEAT_MS)
        .note(
            "Llama 3.1 405B at 16 bits per weight is about 810 GB. In SanDisk's simulation, reading its weights from HBF came within 2.2% of an HBM with unlimited capacity.",
            "Green beads drop into the top of the flash stack; between the stacks a grey bar rises for unlimited HBM and a teal bar beside it stops just short of it.",
        )
        .detail(
            "A company simulation, not a measured part.",
            &["~810 GB of weights", "Within 2.2% of unlimited HBM"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
