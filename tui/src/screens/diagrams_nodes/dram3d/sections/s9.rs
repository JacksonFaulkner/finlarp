// R&D tab, 3D DRAM: section 9 (heading 9 of diagrams_pages/RND_3D_DRAM.txt), "Who is building it,
// timing and risks". Blender scene tools/pbr3d/blender/rnd_3d_dram_section_9.py, GLB
// tools/pbr3d/assets/rnd_3d_dram_section_9.glb. Three beats: Samsung's reported node road, one plinth
// per company with what it is building, and the risks.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_3d_dram_section_9.glb"),
        BEATS,
    )
}

/// The three beats (match rnd_3d_dram_section_9.py).
const BEATS: &[Beat] = &[
    Beat::new("Samsung's reported road", BEAT_MS)
        .note(
            "Samsung (005930.KS) reportedly made working 10a dies from March 2026 wafers. The reported plan is development in 2026, qualification in 2027 and mass production in 2028, with 4F2 VCT across 10a, 10b and 10c and 3D DRAM from 10d; a roadmap slide puts stacked DRAM in the early 2030s. These are press reports and targets; Samsung has not committed to the schedule.",
            "Four plinths along a road: VCT cells on the first three (10a, 10b, 10c) and a block of stacked sideways cells on the fourth (10d). A bead runs along the road and each plinth's edge lights green as it passes, the cells' capacitors lighting gold.",
        )
        .detail(
            "Three VCT nodes, then stacking.",
            &["Mass production 2028: target (TrendForce)", "Stacked DRAM early 2030s (Tom's Hardware)"],
        ),
    Beat::new("who is building what", BEAT_MS)
        .note(
            "Samsung leads with VCT. SK hynix (000660.KS) reportedly plans 4F2 at 10b, with periphery bonded under the cells. Micron (MU) skips 4F2: \"It's the capacitor pitch that defines the DRAM.\" China's CXMT plans 4F2 DDR5 server modules (RDIMMs) by the end of 2026, possibly only partly 4F2. NEO Semiconductor claims an IGZO 3D X-DRAM of up to 128 layers.",
            "Five plinths light in turn: a VCT cell for Samsung, a VCT cell on a purple bonded periphery slab for SK hynix, a flat cell with a tall capacitor for Micron, a VCT cell for CXMT and a six-layer stacked block for NEO.",
        )
        .detail(
            "Four bets on 4F2 or stacking, one on staying planar.",
            &["SK hynix 4F2 at 10b (TrendForce)", "CXMT 4F2 RDIMMs end-2026: plan (TrendForce)", "NEO 128 layers: claim (Blocks and Files)"],
        ),
    Beat::new("the risks", BEAT_MS)
        .note(
            "No 4F2 or stacked DRAM is on sale; every date is a company target or a press report. Extra process steps and new materials can eat the density gain, so smaller cells may not mean cheaper bits. And stacked DRAM needs dozens to hundreds of layers before it pays.",
            "Seen from the other side, a red line glows along the front of all five plinths. Orange slabs drop one by one onto a pile beside the Samsung cell, and grey ghost layers keep appearing, one above another, over the stacked block.",
        )
        .detail(
            "Density on paper is not cost per bit.",
            &["Nothing on sale yet (Bits&Chips)", "32-300 layers needed (TrendForce, SemiEngineering)"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
