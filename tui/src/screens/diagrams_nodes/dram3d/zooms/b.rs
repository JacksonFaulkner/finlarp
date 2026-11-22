// R&D tab, 3D DRAM: zoom-in b, "periphery bonded under the array" (tools/pbr3d/blender/rnd_3d_dram_zoom_b.py,
// GLB tools/pbr3d/assets/rnd_3d_dram_zoom_b.glb). The cell wafer turned face down onto the periphery
// wafer, the copper pads meeting at the bond, then a signal from a cell down into the sense amps.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_3d_dram_zoom_b.glb"),
        BEATS,
    )
}

const BEATS: &[Beat] = &[
    Beat::new("two wafers, face to face", BEAT_MS)
        .note(
            "The cell arrays and the periphery are made on separate wafers: the periphery with a logic process, the cells with a DRAM process. The cell wafer is turned face down and bonded onto the periphery wafer, wafer to wafer.",
            "A wafer of teal dies hangs above a wafer of purple dies. The top wafer flips over, showing its bare grey back, comes down onto the purple wafer, and a white ring glows at the seam.",
        )
        .detail(
            "Samsung calls it cell-on-peripheral (COP) [1].",
            &["periphery wafer: logic process [2]", "W2W hybrid Cu bonding [1]"],
        ),
    Beat::new("copper meets copper", BEAT_MS)
        .note(
            "At the bond face each wafer carries copper pads set in oxide. The two faces press together: oxide bonds to oxide and each pad lands on its partner, so the wires join with no bumps in between.",
            "Close on one die's bond face: the cell array, its bit line and a row of copper pads hang above a white oxide face with matching pads, then come down until pad sits on pad, and a white line glows along the seam.",
        )
        .detail(
            "Every pad on the wafer joins in the same bonding step.",
            &["pad to pad, oxide to oxide", "hybrid Cu bonding [1]"],
        ),
    Beat::new("sense amps right under the cells", BEAT_MS)
        .note(
            "Now a cell's charge goes down its bit line, through a via and the bond, into the sense amps directly below. With the periphery under the array instead of beside it, the die shrinks; Samsung says its test chip gets over 20% more dies per wafer at the same design rules.",
            "The whole die cut open: four capacitors on their pillars over a glowing bond line. One word line and the front bit line light, beads drop through the bond into the periphery, and the purple sense-amp block below lights between two green decoder blocks.",
        )
        .detail(
            "The periphery stops taking floor space beside the array.",
            &[">20% more dies per wafer (Samsung) [1]", "16 Gb test chip reads and writes [1]"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
