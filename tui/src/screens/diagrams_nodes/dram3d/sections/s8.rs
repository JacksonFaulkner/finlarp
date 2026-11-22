// R&D tab, 3D DRAM: section 8 (heading 8 of diagrams_pages/RND_3D_DRAM.txt), "The weak spot: the
// floating body". Blender scene tools/pbr3d/blender/rnd_3d_dram_section_8.py, GLB
// tools/pbr3d/assets/rnd_3d_dram_section_8.glb. Three beats: why a pillar's body floats and a planar
// body does not, SK hynix's shared back gate, and the junctionless IGZO channel.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_3d_dram_section_8.glb"),
        BEATS,
    )
}

/// The three beats (match rnd_3d_dram_section_8.py).
const BEATS: &[Beat] = &[
    Beat::new("why the pillar's body floats", BEAT_MS)
        .note(
            "In a flat transistor the body is part of the silicon underneath, so stray charge (holes) made while it switches drains away. In a vertical pillar the body is cut off from the silicon below by the n+ region and the bit line, so the charge builds up in it and changes how the transistor switches.",
            "Left, a flat cell: its buried word line and channel glow, and pink beads run down out of the channel into the grey silicon. Right, a VCT pillar: its word line and channel glow too, but pink hole balls appear in the tan body one by one, stacking up, and the body turns red.",
        )
        .detail(
            "The pillar has nowhere to send the charge.",
            &["Charge builds in the body (Bits&Chips)", "Planar body tied to the substrate"],
        ),
    Beat::new("fix one: a back gate", BEAT_MS)
        .note(
            "SK hynix's 4F2 vertical-gate cell at VLSI 2026 puts a shared back-gate transistor between pairs of cells to control their threshold voltage. Drawn here as two pillars with their word lines outside and one back gate in the gap between them.",
            "Two pillars with charged capacitors, a maroon word line on the outer side of each and an orange block between them. Pink holes sit in both bodies; the orange back gate lights up, the holes slide into it and vanish, and on the Id-Vg plot to the left the bright curve slides right, back onto the dim reference curve.",
        )
        .detail(
            "A second gate holds the threshold where it should be.",
            &["4F2 VG + shared back gate (SK hynix, VLSI 2026)", "Bit-line shielding, fusion bonding (VLSI 2026)"],
        ),
    Beat::new("fix two: an oxide channel", BEAT_MS)
        .note(
            "Kioxia and Nanya replaced the silicon channel with IGZO, an oxide semiconductor, in a junctionless vertical transistor. They report it immune to the floating-body effect, with leakage below 1 aA, on-current of 15 uA and retention over 100 seconds (IEDM 2024). Samsung is reportedly also moving its VCT channel to IGZO.",
            "Two pillars side by side. In the silicon one, pink holes fill the tan body, it turns red, beads leak out of its capacitor down into the bit line and the capacitor's gold rim goes dark. The IGZO one is a single green channel with no n+ ends; its capacitor stays lit gold all beat.",
        )
        .detail(
            "No body to charge, and almost no leakage.",
            &["< 1 aA leakage, > 100 s retention (Kioxia/Nanya, IEDM 2024)", "15 uA on-current (IEDM 2024)"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
