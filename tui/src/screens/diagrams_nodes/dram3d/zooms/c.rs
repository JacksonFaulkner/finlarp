// R&D tab, 3D DRAM: zoom-in c, "the stacked layers cut open" (tools/pbr3d/blender/rnd_3d_dram_zoom_c.py,
// GLB tools/pbr3d/assets/rnd_3d_dram_zoom_c.glb). Eight layers of sideways 1T1C cells: one layer close,
// the layers pulled apart and one read into the vertical bit line, then the word-line staircase from behind.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_3d_dram_zoom_c.glb"),
        BEATS,
    )
}

const BEATS: &[Beat] = &[
    Beat::new("a cell lying on its side", BEAT_MS)
        .note(
            "Each layer holds 1T1C cells turned on their side. From the vertical bit line outward: an n+ drain, a thin silicon channel with the word line wrapped all round it (gate-all-around), an n+ source, and a capacitor lying flat along the layer.",
            "Close on the top layer, cut open at the front: a teal bit-line column on the left, a blue strip running right through a tan channel boxed in by maroon word-line bars above and below, then a long grey capacitor with a gold rim. The word line lights pink at the end.",
        )
        .detail(
            "The same 1T1C cell, laid flat so layers can stack.",
            &["GAA cell transistors [8]", "horizontal capacitors [8]"],
        ),
    Beat::new("one bit line through every layer", BEAT_MS)
        .note(
            "Layers are separated by oxide and share vertical bit lines that run down through the stack. Each layer has its own word line, so lighting one picks one layer: its capacitor empties through its transistor into the bit line and down to the sense amps.",
            "The whole eight-layer block: the layers pull apart, the top ones furthest, and settle back. One layer's word line lights pink, the centre bit line glows cyan top to bottom and beads run from a capacitor into it.",
        )
        .detail(
            "Samsung's VLSI 2026 VS-DRAM has 16 layers [8].",
            &["vertical bit lines, horizontal word lines [8]", "8 of 16 layers drawn"],
        ),
    Beat::new("every layer needs its own step", BEAT_MS)
        .note(
            "Each layer's word line has to be wired out, so the layers end in a staircase at the back, as in 3D NAND, with one contact landing on each step. More layers mean more steps; SK hynix showed 5 layers in 2024 and says 32 to 192 are needed for wide use.",
            "Seen from behind and above: grey capacitor ends on the left, maroon word lines stepping out further for each lower layer, a grey contact rising from every step. One layer's step and contacts light pink.",
        )
        .detail(
            "Layer count is the cost lever, and the yield risk.",
            &["SK hynix 5 layers, 56.1% yield [9]", "32-192 layers needed [9]"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
