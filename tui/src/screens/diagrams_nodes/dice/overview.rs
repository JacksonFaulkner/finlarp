// DICE page overview: a Blender scene (tools/pbr3d/blender/dice_overview.py, GLB
// tools/pbr3d/assets/dice_overview.glb). One wafer on blue dicing tape in a steel ring frame: a
// blade cuts a street, a stealth laser focuses inside the silicon, a laser grooves the low-k
// street before the blade finishes, and the tape is stretched so the good die lift off.

use super::super::blender::{Cell, Page, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/dice_overview.glb"),
        beats: BEATS,
        zooms: &[],
    })
}

/// The six beats of the overview, one per step (match dice_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("thinned wafer on tape", BEAT_MS)
        .note(
            "After grinding, the wafer is thin and fragile. It is laminated onto blue dicing tape stretched across a steel ring frame, so the saw, the laser and the picker can all grip it. A 300 mm wafer leaves the fab about 775 um thick and is ground down to 50-200 um first.",
            "A wafer lies on blue tape inside a grey steel ring, its die drawn as a grid across the face. The camera pulls back to show the whole frame on the bench.",
        )
        .detail(
            "The frame turns a floppy wafer into a rigid part.",
            &["775 um out of the fab, ground to 50-200 um", "Dicing tape stretched on a ring frame"],
        ),
    Beat::new("streets: the lanes between die", BEAT_MS)
        .note(
            "Each die is cut out along scribe streets, the empty lanes between die where test structures sit. Blade-cut streets are typically 60-100 um wide, and the street width sets how many die fit on the wafer: narrowing the street on a 0.5 mm die from 80 um to 20 um gives about 24% more die.",
            "Close on the grid: the die are dark squares, and the silicon lanes between them are the streets. The blade and the laser will run down these lanes.",
        )
        .detail(
            "Narrower streets, more die per wafer.",
            &["Blade streets: 60-100 um typical", "0.5 mm die: 20 um vs 80 um street = +24.5% die (computed)"],
        ),
    Beat::new("blade: a diamond saw in water", BEAT_MS)
        .note(
            "A thin diamond blade spins at 15,000 to 30,000 rpm and cuts down the street, cooled and flushed with water. It cuts through the wafer and into the tape but not through the tape, so the die stay held. The risk is edge chipping: a chip over 5-10 um can disqualify a die.",
            "A thin metal blade sits in a dark street and drives down through the silicon into the blue tape. A cut line opens behind it along the street.",
        )
        .detail(
            "Blades are proven and cheap, but the cut is mechanical.",
            &["15,000-30,000 rpm for general dicing", "Chips over 5-10 um may disqualify die", "Blade cuts into the tape, not through it"],
        ),
    Beat::new("stealth: laser inside the silicon", BEAT_MS)
        .note(
            "A stealth laser is focused at a point inside the silicon, where its light passes through the surface. The focus makes a modified layer of microcracks inside the wafer, and the tape is then stretched to split it along the lines. There is no blade, so there is no kerf. DISCO's SDBG process grinds the wafer after this step, removing the modified layer and reducing front and back chipping.",
            "The wafer is drawn see-through. A laser spot moves along a street deep inside the silicon, leaving a glowing crack plane behind it.",
        )
        .detail(
            "The cut happens inside the wafer, not on its surface.",
            &["No blade, so no kerf", "SDBG: grind after stealth; fewer front and back chips"],
        ),
    Beat::new("low-k: groove first, then blade", BEAT_MS)
        .note(
            "Low-k films are porous and brittle, and a blade alone can chip or peel them. Logic wafers are now usually grooved first: a laser cuts through the low-k film in the street, and then a blade finishes the cut. Laser grooving followed by a blade is standard for logic wafers.",
            "Two dark grooves are burned into the top of the street by the laser, then the blade comes down the middle to finish the cut between them.",
        )
        .detail(
            "Grooving protects the fragile film from the blade.",
            &["Low-k: porous, brittle, chips and delaminates", "Laser grooving, then blade: standard for logic wafers"],
        ),
    Beat::new("tape stretched: good die lift off", BEAT_MS)
        .note(
            "The tape is stretched, which opens gaps between the die. The wafer map from wafer sort tells the picker which die to skip, so bad die stay on the tape and only known-good die are lifted off for packaging. A die that is chipped at the edge can crack later and fail in the field.",
            "The die spread apart on the blue tape. The red die stay where they are, and the blue die lift off one at a time above the tape.",
        )
        .detail(
            "Only good die go on to packaging.",
            &["Stretch the tape to open gaps", "Wafer map marks the bad die", "Good die are picked; DAF die go straight to die attach"],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_captioned_and_has_six_beats() {
        let s = build();
        assert_eq!(s.beats().len(), 6);
        super::super::super::blender::explained(s.as_ref(), "DICE overview");
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "DICE overview");
    }
}
