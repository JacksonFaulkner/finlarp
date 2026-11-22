// R&D tab, 3D DRAM: zoom-in e, "the floating body" (tools/pbr3d/blender/rnd_3d_dram_zoom_e.py, GLB
// tools/pbr3d/assets/rnd_3d_dram_zoom_e.glb). A VCT pillar's body filling with holes, the threshold
// curve sliding, then the two fixes: a back gate and a junctionless IGZO channel.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_3d_dram_zoom_e.glb"),
        BEATS,
    )
}

const BEATS: &[Beat] = &[
    Beat::new("a body with nowhere to drain", BEAT_MS)
        .note(
            "In a planar transistor the p-type body is part of the silicon wafer, so stray charge drains away. In a VCT pillar the body sits between two n+ layers, over the bit line and oxide, with no tie to the silicon. Holes made while the transistor switches have nowhere to go and pile up.",
            "Close on one pillar, cut open: blue n+ layers top and bottom, the tan body between maroon word-line blocks, a teal bit line and grey oxide underneath. Pink dots appear one by one in the body until it glows pink.",
        )
        .detail(
            "The pillar that saves area also cuts the body off.",
            &["charge builds in the body [5]"],
        ),
    Beat::new("the threshold slides", BEAT_MS)
        .note(
            "Charge in the body lowers the transistor's threshold voltage, so it turns on earlier than designed and leaks when it should be off. The capacitor slowly loses its charge into the bit line even with the word line low, and the bit fades sooner.",
            "An Id-Vg plot beside the pillar: the bright curve slides left of its grey reference. Beads trickle from the capacitor down the pillar and the bit line glows while the word line stays dark.",
        )
        .detail(
            "A shifting threshold means leakage and shorter retention.",
            &["changes how the transistor switches [5]"],
        ),
    Beat::new("two fixes: back gate, IGZO", BEAT_MS)
        .note(
            "SK hynix's VLSI 2026 4F2 VG cell adds a shared back-gate transistor beside the channel to hold the threshold voltage. Kioxia and Nanya's OCTRAM skips the p-type body altogether: a junctionless IGZO oxide channel, reported immune to the floating-body effect, with leakage below 1 aA.",
            "Two cells side by side. Left: a silicon pillar with the word line on one side and a green back gate on the other; holes appear, the back gate glows and they vanish. Right: a pillar made of one pale teal IGZO block with no n+ layers, the word line on both sides.",
        )
        .detail(
            "Control the body, or remove it.",
            &["back gate holds Vt (SK hynix VG) [8]", "IGZO: leak <1 aA, retention >100 s [10]"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
