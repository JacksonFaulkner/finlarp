// R&D tab, HBF: zoom-in b, CBA bonding. One NAND die drawn large: the CMOS logic wafer and the
// NAND array wafer built apart, bonded face to face, and the bonded die dropped onto its stack
// (tools/pbr3d/blender/rnd_hbf_zoom_b.py -> tools/pbr3d/assets/rnd_hbf_zoom_b.glb).

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static CELL: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    page(
        &CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/rnd_hbf_zoom_b.glb"),
        BEATS,
    )
}

/// The three beats (match rnd_hbf_zoom_b.py).
const BEATS: &[Beat] = &[
    Beat::new("two wafers, face to face", BEAT_MS)
        .note(
            "A NAND die is built from two wafers. The CMOS logic that drives the flash is made on one, and the memory array on the other, each in the process that suits it.",
            "A dark grey logic wafer below with gold circuit patches on its cut face, and a teal array wafer hanging above it with pale vertical NAND strings, the two facing each other.",
        )
        .detail(
            "Logic and memory each get their own wafer.",
            &["CMOS logic wafer", "NAND array wafer"],
        ),
    Beat::new("bonded into one die", BEAT_MS)
        .note(
            "The array wafer comes down onto the logic and the two are bonded directly together. SanDisk calls this CBA: CMOS directly bonded to array.",
            "The teal array layer drops onto the grey logic layer, and a pale line glows along the seam where they bond.",
        )
        .detail(
            "Two wafers become one die.",
            &["CBA: CMOS bonded to array", "SanDisk's die design"],
        ),
    Beat::new("logic under the array", BEAT_MS)
        .note(
            "With the logic underneath, every block of the array has its circuits right below it, and the array keeps its area for bits. The bonded die then drops onto the stack, one of sixteen.",
            "The bonded die settles onto a stack of teal and grey dies on a blue base die; small green strips light under each block of strings.",
        )
        .detail(
            "Building the logic on its own wafer frees the array's area.",
            &["Logic under every array block", "16 dies to a stack"],
        ),
];

#[cfg(test)]
mod tests {
    #[test]
    fn three_beats() {
        assert_eq!(super::BEATS.len(), 3);
    }
}
