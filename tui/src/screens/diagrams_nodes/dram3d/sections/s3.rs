// R&D tab, 3D DRAM: section 3 (heading 3 of diagrams_pages/RND_3D_DRAM.txt), "From planar to stacked,
// in order". Blender scene tools/pbr3d/blender/rnd_3d_dram_section_3.py, GLB
// tools/pbr3d/assets/rnd_3d_dram_section_3.glb. The five numbered steps happen on one spot, each
// replacing the last: planar cells and their stretching capacitors, the VCT array and its periphery
// sliding underneath, and a stack of sideways cells.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_3d_dram_section_3.glb"),
        BEATS,
    )
}

/// The three beats (match rnd_3d_dram_section_3.py).
const BEATS: &[Beat] = &[
    Beat::new("1-2: flat cell, shrinking stalls", BEAT_MS)
        .note(
            "Step 1: today's cell lies flat, the transistor in the silicon and a tall capacitor on top, about 6F2. Step 2: to shrink it the capacitor gets narrower, and a narrower capacitor has to grow taller to hold the same charge.",
            "Two planar cells cut open. A word line glows and beads run into the bit line; then both capacitors squeeze thinner and stretch upward.",
        )
        .detail(
            "Shrinking the flat cell runs into the capacitor.",
            &["6F2 = 2F x 3F (Bits&Chips)", "Tall capacitors yield poorly (SemiEngineering)"],
        ),
    Beat::new("3-4: pillar, then periphery under", BEAT_MS)
        .note(
            "Step 3: the transistor stands up as a pillar with the capacitor on top, a 4F2 cell. Step 4: the periphery moves to its own wafer and is bonded underneath the cell array.",
            "The planar cells sink away and a 2 by 2 VCT array rises in their place, a tile flashing over it. Then a grey periphery block slides in from the side under it, a pale bond line glows, and the purple and green circuit blocks inside light up.",
        )
        .detail(
            "Stand the transistor up, then move the circuits underneath.",
            &["4F2 = 2F x 2F (Bits&Chips)", "W2W hybrid Cu bond (Samsung, ISSCC 2026)"],
        ),
    Beat::new("5: cells on their sides, in layers", BEAT_MS)
        .note(
            "Step 5: the cells are laid on their sides and stacked in layers that share a vertical bit line. Samsung's VLSI 2026 paper shows 16 layers; SK hynix says 32-192 layers are needed for wide use.",
            "The VCT die sinks and a stack builds up on the same spot, one layer at a time: white slabs, each with sideways transistors and long gold-rimmed capacitors on both sides of a teal bit line. The bit line glows and beads run down it from one layer.",
        )
        .detail(
            "The last step goes up in layers.",
            &["16 layers (Samsung VS-DRAM, VLSI 2026)", "32-192 layers needed (SK hynix)"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
