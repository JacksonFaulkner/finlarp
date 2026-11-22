// R&D tab, 3D DRAM: zoom-in a, "the vertical transistor cut open" (tools/pbr3d/blender/rnd_3d_dram_zoom_a.py,
// GLB tools/pbr3d/assets/rnd_3d_dram_zoom_a.glb). Three 4F2 VCT cells on one buried bit line, cut open:
// the whole cell, the pillar with its word line switching on, then a read down into the bit line.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_3d_dram_zoom_a.glb"),
        BEATS,
    )
}

const BEATS: &[Beat] = &[
    Beat::new("a transistor standing up", BEAT_MS)
        .note(
            "A 4F2 cell stands its transistor up as a pillar. The bit line is buried at the bottom, the word line wraps the pillar halfway up, and the capacitor sits directly on top, so the transistor takes no more floor space than the capacitor.",
            "Three cells in a row, cut open at the front: a teal bit line along the bottom, short blue-and-tan pillars with maroon word-line blocks either side, tall grey capacitors with glowing gold rims, and a green 2F x 2F tile floating above the middle cell.",
        )
        .detail(
            "Transistor and capacitor share one 2F x 2F footprint.",
            &["4F2 = 2F x 2F [5]", "capacitor directly on top [2]"],
        ),
    Beat::new("the word line opens the channel", BEAT_MS)
        .note(
            "Inside the pillar: an n+ layer on the bit line, a p-type body, and an n+ layer under the capacitor, with thin gate oxide round the body. When the word line goes high it pulls electrons to the body's faces and a channel forms from top to bottom.",
            "Close on the middle pillar: blue n+ ends, a tan body edged in yellow oxide, maroon word-line blocks on both sides. The word-line blocks light pink, then thin cyan strips light along both faces of the body.",
        )
        .detail(
            "The word line is the gate, wrapped round the pillar [6].",
            &["word line wraps the pillar [6]", "bit line connects at the source [6]"],
        ),
    Beat::new("charge drops into the bit line", BEAT_MS)
        .note(
            "With the channel open, the capacitor's charge runs straight down the pillar into the bit line, which carries it sideways to a sense amp. The neighbours share the bit line but sit on their own word lines, so they stay shut.",
            "The middle capacitor's gold fill drains from the top down; beads fall through the pillar into the bit line, which glows cyan along the whole row while the neighbours' capacitors stay lit.",
        )
        .detail(
            "Vertical path: capacitor, pillar, bit line.",
            &["Samsung 16 Gb VCT test chip reads and writes [1]"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
