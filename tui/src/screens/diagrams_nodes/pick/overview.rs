// PICK: the page's overview, a Blender scene (tools/pbr3d/blender/pick_overview.py, GLB
// tools/pbr3d/assets/pick_overview.glb). A sawn wafer on blue tape, the map panel, a collet that lifts
// one good die by vacuum while needles push it off the tape, and the carrier tray; the HBM stack at
// right shows why one bad die scraps a whole stack.

use super::super::blender::{Cell, Page, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/pick_overview.glb"),
        beats: BEATS,
        zooms: &[],
    })
}

/// The six beats of the overview, one per step (match pick_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("good die only", BEAT_MS)
        .note(
            "After wafer sort, the wafer is sawn into single die that stay on blue tape. A pick-up tool lifts only the die the map marks good and sets them into a carrier. The rest are left behind on the tape.",
            "A round wafer on blue dicing tape in a steel frame, cut into a grid of die. A map panel at left shows green for good and red for bad. A collet hangs over the centre die, and a white carrier tray sits at right.",
        )
        .detail(
            "Only die the map marks good are lifted.",
            &[
                "Passing die are separated from failing die by pre-set characteristics (Syagrus)",
                "Carriers: waffle pack, Gel-Pak, tape and reel, or custom tray (Syagrus)",
            ],
        ),
    Beat::new("the map decides", BEAT_MS)
        .note(
            "The sorter works from the wafer map, a file with one entry per die position. Good or bad, plus the wafer ID and orientation. Some sorters read ink dots on the wafer instead. The picker skips the rejects, so a bad die is never bonded.",
            "The map panel fills the left of the frame, one square per die: green for good, red for bad. The wafer sits at right with the same red dies in place. The collet waits above the centre die, which is green.",
        )
        .detail(
            "The map is the picker's only record of good and bad.",
            &[
                "Wafer map import, or ink dot recognition (Syagrus)",
                "Electronic wafer map input (Royce MP300)",
            ],
        ),
    Beat::new("vacuum holds the tape", BEAT_MS)
        .note(
            "The sawn wafer sits on a vacuum chuck, which holds the tape flat. The collet comes down onto the chosen die and holds it by vacuum, then the die is ready to be lifted.",
            "The collet drops from above, its vacuum hose rising behind it. Under the tape a dark chuck holds the wafer. The die is still flat on the tape, and the neighbouring die are unmoved.",
        )
        .detail(
            "A soft vacuum tip takes the die.",
            &[
                "Chuck holds the tape by reduced pressure (US 7498241)",
                "Standard soft surface-contact vacuum pick-up (Royce MP300)",
            ],
        ),
    Beat::new("needles push the die off", BEAT_MS)
        .note(
            "Needles rise through the tape from below and push the die up, peeling the tape away from it. Needles set close together peel the tape evenly. The collet then lifts the die clear. A thin die can crack at this step.",
            "Four needle tips poke up under the centre die, and the die rises off the tape. The collet, with its hose, lifts it upward and away from the wafer.",
        )
        .detail(
            "Needle spacing and die thickness decide whether the die survives.",
            &[
                "Narrow needle spacing peels tape evenly (US 7498241)",
                "Thin die: crack or chip risk at pick-up (US 7498241)",
                "Eject height up to 3 mm (Royce MP300)",
            ],
        ),
    Beat::new("into the carrier", BEAT_MS)
        .note(
            "The collet swings the die across to a carrier. Good die are packed into trays, waffle packs, Gel-Paks or tape and reel, whichever the next step needs. The neighbouring die stay on the tape.",
            "The collet carries the die over to the white tray at right and sets it down. The rest of the wafer, including the die next to the picked one, stays on the tape.",
        )
        .detail(
            "The carrier follows the next step.",
            &[
                "Trays, waffle packs, Gel-Pak, tape and reel (Syagrus)",
                "Waffle pack or Gel-Pak up to 16 x 2 in (Royce MP300)",
            ],
        ),
    Beat::new("known good die", BEAT_MS)
        .note(
            "An HBM stack is only as good as its worst die. A 12-high HBM3E stack holds twelve DRAM dies on a base die, and one bad die scraps the whole stack. Known-good-die testing checks each die before packaging, so only good die are assembled.",
            "The HBM stack at right: a dark base, twelve thin dies, and one red die in the middle. The red die is the single failure that scraps the whole stack.",
        )
        .detail(
            "One bad die scraps the whole module.",
            &[
                "HBM3E 12-high: 13 dies, 88% module yield at 99% per die (SemiconductorX)",
                "KGD is tested on the naked die before packaging (Synopsys)",
                "HBM stacks up to 8 DRAM dies, 16 in HBM4 (FormFactor)",
            ],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_captioned_and_keyed() {
        let s = build();
        assert_eq!(s.beats().len(), 6);
        super::super::super::blender::explained(s.as_ref(), "PICK overview");
        assert!(s.zooms().is_empty());
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "PICK overview");
    }
}
