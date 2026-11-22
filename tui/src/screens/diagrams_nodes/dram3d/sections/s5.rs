// R&D tab, 3D DRAM: section 5 (heading 5 of diagrams_pages/RND_3D_DRAM.txt), "The 4F2 cell: a vertical
// channel transistor". Blender scene tools/pbr3d/blender/rnd_3d_dram_section_5.py, GLB
// tools/pbr3d/assets/rnd_3d_dram_section_5.glb. Three beats: the pillar's parts, the word line wrapped
// round it as the gate during a write, and the reported material changes (IGZO channel, Mo word line).

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_3d_dram_section_5.glb"),
        BEATS,
    )
}

/// The three beats (match rnd_3d_dram_section_5.py).
const BEATS: &[Beat] = &[
    Beat::new("source, channel, drain in one pillar", BEAT_MS)
        .note(
            "In a vertical channel transistor the source, channel and drain sit in one upright pillar: an n+ end on the bit line, the silicon channel, and an n+ end under the capacitor. So the transistor takes no more floor than the capacitor above it.",
            "Close on a cell cut open: a tan pillar with blue n+ ends, framed by yellow gate oxide, maroon word-line bars either side, a teal bit line underneath and a gold-rimmed capacitor right on top. A whole, uncut cell stands behind it.",
        )
        .detail(
            "The transistor fits under its own capacitor.",
            &["4F2 = 2F x 2F (Bits&Chips)"],
        ),
    Beat::new("the word line wraps the pillar", BEAT_MS)
        .note(
            "The word line wraps the pillar as the gate, and the bit line connects at the source. Turning the word line on opens the channel and lets charge flow between the bit line and the capacitor.",
            "From high on the left: the whole cell's word line glows pink all round its pillar. In the cut cell the word line lights, the channel edges glow cyan, the bit line glows, and beads climb from the bit line up the pillar into the capacitor, which fills with gold.",
        )
        .detail(
            "Gate all round the pillar, bit line below.",
            &["Word line wraps the pillar (TweakTown)"],
        ),
    Beat::new("new materials: IGZO and molybdenum", BEAT_MS)
        .note(
            "Charge slowly leaks out through the transistor. Samsung is reported to be moving the channel from silicon to IGZO, an oxide that leaks very little, and to be weighing molybdenum to replace titanium nitride in the word line. Both are reports, not announced choices.",
            "Red beads trickle from the capacitor down the silicon pillar and away along the bit line. Then the pillar turns sea-green (IGZO) and the leak stops, and the word-line bars beside it turn silver (molybdenum).",
        )
        .detail(
            "Less leakage, longer hold.",
            &["Si to IGZO channel (TrendForce, reported)", "Mo for TiN word line (TrendForce, reported)"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
