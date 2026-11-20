// WAFER SORT: the page's overview, a Blender scene (tools/pbr3d/blender/wafer_sort_overview.py, GLB
// tools/pbr3d/assets/wafer_sort_overview.glb). One test cell: the ATE tester and its cables, the test head,
// the probe card with its needles, the wafer on a vacuum chuck with a prober cursor, and the wafer map monitor.

use super::super::blender::{Cell, Page, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/wafer_sort_overview.glb"),
        beats: BEATS,
        zooms: &[],
    })
}

/// The six beats of the overview, one per step (match wafer_sort_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("probe each die, before the cut", BEAT_MS)
        .note(
            "Wafer sort is the first electrical test of the chips. While every die is still on the wafer, a tester drives signals into it through a probe card and reads the answer. The result is kept die by die, so a bad die is never cut, packaged or paid for.",
            "The whole test cell, left to right: the tester cabinet, four cables up to the test head, the probe card hanging under the head, the grey wafer on its chuck, and the wafer map monitor on the right. Yellow beads run along the cables.",
        )
        .detail(
            "Testing happens before dicing and packaging.",
            &["Also called EDS, CP or WT testing", "Bad die are marked and skipped later"],
        ),
    Beat::new("the prober steps die to die", BEAT_MS)
        .note(
            "The prober holds the wafer on a vacuum chuck and cameras align its pattern. The chuck then moves so the probes reach one die after another. The vacuum is strong but temporary, so the next wafer loads quickly.",
            "A cyan cursor sits on one grey die and steps along a row of dies. The probe card is up, clear of the wafer, and the chuck stays put while the cursor moves.",
        )
        .detail(
            "Optical alignment, then die-to-die stepping.",
            &["Cameras align the wafer's pattern", "Vacuum hold on the chuck: quick to load and unload"],
        ),
    Beat::new("needle tips land on the pads", BEAT_MS)
        .note(
            "Each probe is a fine needle or spring tip. The card presses down until the tips touch the bond pads on each die, so current can pass into the chip. Several dies are probed at once to cut test time.",
            "The card drops and the gold needles reach down onto the four cyan-lit dies, one needle per pad. The tips sink a little past first touch, the overdrive that keeps the contact firm.",
        )
        .detail(
            "Tips touch the pads; the card presses them down.",
            &[
                "HBM microbumps: about 25 um across, 45 um pitch (FormFactor)",
                "Advanced-packaging card: MEMS springs at 45 um contact pitch (FormFactor)",
            ],
        ),
    Beat::new("the tester judges every die", BEAT_MS)
        .note(
            "The tester is the instrument. It applies power and test patterns through the head and the card, reads each die's response and compares it with the limits. Advantest and Teradyne make most of these testers.",
            "Beads run down the four cables from the tester into the test head and the card, then back up carrying the answers. The tags name the tester and the card that carries the tips.",
        )
        .detail(
            "The tester sorts each die into a bin.",
            &[
                "Bins are grouped as good or bad",
                "Advantest and Teradyne: roughly 85-90% of testers, combined, 2025 (estimates)",
            ],
        ),
    Beat::new("the map keeps one bin per die", BEAT_MS)
        .note(
            "Each die's result is stored by its position as a bin, which gives a pass/fail map. The map follows the wafer through the rest of production. Clusters near the wafer edge can point to a process problem.",
            "The map on the right fills in one tile per die, in scan order: green for a good die, red for a bad one. The pattern is illustrative, not fab data.",
        )
        .detail(
            "The map is the record for every die.",
            &["Edge clusters can point to process problems", "Pattern in this picture is illustrative, not fab data"],
        ),
    Beat::new("good die move on, bad die stay", BEAT_MS)
        .note(
            "The map is sent on to dicing and to the pick step, which lifts only the passing die. Bad die are skipped, so no assembly cost goes into them. Known-good die are what keep the system yield up.",
            "Beads leave the monitor toward the right, carrying the map to the next step. The green tiles stay lit, and the red ones are the die that will not be picked.",
        )
        .detail(
            "Only known-good die are packaged.",
            &["Known-good die are vital to system yield", "Yield = good die / total die"],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_captioned_and_draws_every_beat() {
        let s = build();
        assert_eq!(s.beats().len(), 6);
        super::super::super::blender::explained(s.as_ref(), "WAFER SORT overview");
        super::super::super::blender::draws_every_beat(s.as_ref(), "WAFER SORT overview");
    }
}
