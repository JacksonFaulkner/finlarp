// COAT page: the overview, a Blender scene (tools/pbr3d/blender/coat_overview.py, GLB
// tools/pbr3d/assets/coat_overview.glb). One coater-developer track in a single row: the carrier port,
// the primer plate, the BARC cup, the resist cup, the soft-bake plate, the chill plate, the interface
// buffer and the scanner. One wafer rides the robot arm from station to station.

use super::super::blender::{Cell, Page, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/coat_overview.glb"),
        beats: BEATS,
        zooms: &[],
    })
}

/// The six beats of the overview, one per step (match coat_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("one track, many modules", BEAT_MS)
        .note(
            "Resist goes on in a coater-developer track, one machine that holds coating cups, hot plates and chill plates in a single line. A robot arm carries each wafer from the carrier port through the modules, then hands it to the scanner through an interface buffer.",
            "The whole track, left to right: the carrier port, the primer plate, the BARC cup, the resist cup, the soft-bake plate, the chill plate, the interface buffer and the scanner. A wafer leaves the carrier port, carried high on the robot arm toward the primer.",
        )
        .detail(
            "Coat, bake and chill share one track.",
            &[
                "TEL ACT-8: coaters, developer, hot plates and chill plates in one machine (EPFL CMi)",
                "In-line with the ASML scanner through an interface block (EPFL CMi)",
            ],
        ),
    Beat::new("prime, then anti-reflect", BEAT_MS)
        .note(
            "Resist sticks poorly to a bare wafer, so the wafer first gets a primer that helps it bond. Many stacks then get a bottom anti-reflective coating (BARC), a thin layer that stops light bouncing off the film below and blurring the pattern.",
            "The wafer sits on the primer plate, then glides to the BARC cup, where a dark film appears on its top surface.",
        )
        .detail(
            "A primer first, then an anti-reflect layer.",
            &[
                "HMDS vapour promotes adhesion before coating (EPFL CMi, ACT-8)",
                "The BARC coater is its own cup on the same track (EPFL CMi, ACT-8)",
            ],
        ),
    Beat::new("dispense and spin", BEAT_MS)
        .note(
            "A pump puts a small pool of liquid resist on the centre of the wafer. The wafer spins, the liquid spreads into a thin film, and the excess is flung off the edge. Spin speed sets the thickness: the faster the spin, the thinner the film.",
            "The resist nozzle drops an amber bead on the centre. The wafer turns in its cup while the amber film spreads out, and a few drops fly off the rim into the cup.",
        )
        .detail(
            "Spin speed sets the film thickness.",
            &[
                "MicroChem KMSF 1000 sheet: spin 1000-4000 rpm",
                "MicroChem SPR3000 sheet: 3500-5500 rpm, 30 s, wafers up to 150 mm",
            ],
        ),
    Beat::new("trim the rim", BEAT_MS)
        .note(
            "Spinning leaves a thick ridge of resist around the rim of the wafer. An edge-bead nozzle sprays solvent on the edge only and dissolves the ridge away, so the rim stays clean.",
            "The edge-bead nozzle swings in to the rim and a solvent drop lands on the edge. The ridge fades away while the middle of the film stays as it was.",
        )
        .detail(
            "Solvent trims the edge, not the middle.",
            &[
                "Edge bead: the thick resist ridge left at the rim by spinning",
                "Cup-wash disc keeps the coater cups clean (EPFL CMi, ACT-8)",
            ],
        ),
    Beat::new("soft bake drives off solvent", BEAT_MS)
        .note(
            "A hot plate bakes the wet film for a few minutes. The solvent evaporates, the film firms up, and the wafer is ready for the scanner. The exact temperature and time depend on the resist.",
            "The wafer sits on the hot plate, which glows orange while the film dries.",
        )
        .detail(
            "Bake the solvent out, then hand the wafer on.",
            &[
                "MicroChem KMSF 1000 sheet: soft bake 100 C, 10 min on a hotplate",
                "AZ 10XT reference (TU Delft): prebake 3 min at 110 C on a hotplate",
            ],
        ),
    Beat::new("chill, then the scanner", BEAT_MS)
        .note(
            "A chill plate brings the wafer back to a steady temperature. The interface buffer holds it, and its slots set how long the wafer waits before the post-exposure bake. The scanner then prints the pattern.",
            "The wafer glides onto the blue chill plate, then into the interface buffer. The scanner waits at the far right of the track.",
        )
        .detail(
            "The track sets the timing; the scanner does the print.",
            &[
                "Chill plate: fast cooling between steps (EPFL CMi, ACT-8)",
                "25-slot buffer sets the delay before PEB (EPFL CMi, ACT-8)",
            ],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_captioned_with_six_beats() {
        let s = build();
        assert_eq!(s.beats().len(), 6);
        super::super::super::blender::explained(s.as_ref(), "COAT overview");
        assert!(s.zooms().is_empty());
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "COAT overview");
    }
}
