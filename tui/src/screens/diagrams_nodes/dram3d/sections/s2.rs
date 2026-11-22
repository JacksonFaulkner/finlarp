// R&D tab, 3D DRAM: section 2 (heading 2 of diagrams_pages/RND_3D_DRAM.txt), "The parts". Blender
// scene tools/pbr3d/blender/rnd_3d_dram_section_2.py, GLB
// tools/pbr3d/assets/rnd_3d_dram_section_2.glb. Three beats walking the parts table: a VCT cell pulled
// apart into its parts, the cell array over its bonded periphery, and a stacked VS-DRAM block.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_3d_dram_section_2.glb"),
        BEATS,
    )
}

/// The three beats (match rnd_3d_dram_section_2.py).
const BEATS: &[Beat] = &[
    Beat::new("the cell: 1T1C, VCT, 4F2", BEAT_MS)
        .note(
            "A cell is one transistor and one capacitor (1T1C); the capacitor holds the bit as charge. In a VCT the transistor's source, channel and drain are stacked in one pillar, the word line wraps it as the gate, the bit line runs underneath and the capacitor sits directly on top. The cell is 2F by 2F: 4F2. SK hynix calls its version a vertical gate (VG).",
            "One cell pulls apart: the capacitor and its pad lift up, the two maroon word-line bars slide out to the sides and a third back, the teal bit line drops, leaving the tan pillar with blue n+ ends standing. Then it all snaps back together under a green-edged tile.",
        )
        .detail(
            "Every part stacks over the same 2F x 2F patch.",
            &["4F2 = 2F x 2F (Bits&Chips)", "6F2 today = 2F x 3F (Bits&Chips)"],
        ),
    Beat::new("the chip: periphery bonded under", BEAT_MS)
        .note(
            "The periphery is the sense amps, decoders and I/O that run the array. In cell-on-periphery (COP, also PUC) it is made on its own wafer and the cell wafer is bonded on top by a hybrid bond: copper pads set in oxide, joined face to face, wafer to wafer.",
            "Close on a small array over a grey periphery block. The array lifts a little to show copper pads in a white oxide layer on both faces, then drops back; a pale bond line glows, beads drop through the pads and the purple sense-amp and green decoder blocks light.",
        )
        .detail(
            "Two wafers, one die.",
            &["W2W hybrid Cu bond (Samsung, ISSCC 2026)", "Periphery wafer: logic process (TrendForce)"],
        ),
    Beat::new("stacked: VS-DRAM", BEAT_MS)
        .note(
            "Samsung's stacked DRAM, VS-DRAM, lays the cell on its side: a gate-all-around transistor and a capacitor lying flat in each layer, with the bit line running vertically through all the layers. Two more terms come later on the page: the floating body, where charge piles up in a transistor body with no tie to the substrate, and IGZO, an oxide channel that leaks very little.",
            "A four-layer block seen low from the left. The vertical bit line in the middle glows cyan; layer by layer from the bottom up a pink word line lights and the long capacitors either side fill with gold, while beads climb the bit line.",
        )
        .detail(
            "Cells on their sides, layers on a shared bit line.",
            &["VS-DRAM: 16 layers (Samsung, VLSI 2026)"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
