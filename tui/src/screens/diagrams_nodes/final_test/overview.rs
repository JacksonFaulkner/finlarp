// FINAL TEST: the page's overview, a Blender scene (tools/pbr3d/blender/final_test_overview.py, GLB
// tools/pbr3d/assets/final_test_overview.glb). One test line, left to right: a tray of packaged parts,
// the handler that presses one into a socket, the ATE test head, the burn-in oven, a system test board,
// the speed bins with a fmax bell, and a pallet of sealed trays. Parts ride an overhead rail.

use super::super::blender::{Cell, Page, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/final_test_overview.glb"),
        beats: BEATS,
        zooms: &[],
    })
}

/// The seven beats of the overview, one per step (match final_test_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("packaged parts, last check", BEAT_MS)
        .note(
            "Final test is the last check before a packaged chip ships. A handler feeds packaged parts from trays, tubes or reels, and the tester runs the program that sets each chip's grade: which speed, power or core count it is sold as.",
            "A tray of packaged parts on the left, with the handler's gantry over it. The line runs right, past the test head and the burn-in oven, to the speed bins and the pallet at the far end. Parts ride an overhead rail.",
        )
        .detail(
            "It sets the product grade.",
            &["Last check before shipping", "Catches assembly damage: cracked bumps, broken wire bonds"],
        ),
    Beat::new("the handler presses the part in", BEAT_MS)
        .note(
            "The handler picks each packaged part from its tray and presses it into a socket, where the contacts must touch every ball or lead. High-volume cells test four, eight, sixteen or more parts at once to spread the cost of the tester.",
            "The gantry head drops onto a part in the tray, lifts it, carries it over the load board and presses it down into the socket. The part sits in the socket with its pins touching the board.",
        )
        .detail(
            "Many parts share one tester.",
            &["Handler picks from trays, tubes or reels", "High-volume cells: four to sixteen or more at once"],
        ),
    Beat::new("the tester runs the program", BEAT_MS)
        .note(
            "The tester runs DC, functional, scan and speed tests through the load board. An AI accelerator takes over 20 minutes on the tester, against 30 to 60 seconds for a 5nm phone processor, and test cost has risen from under 2 percent of chip price toward 5 to 7 percent on complex AI packages.",
            "The test head's lights step through the program while beads of signal run along the cable from the load board into the test head. The socket and load board stay in place.",
        )
        .detail(
            "Test time is cost.",
            &["AI accelerator: over 20 min on the tester", "Phone processor: about 30 to 60 s", "Test cost: 5 to 7 percent of chip price on AI packages"],
        ),
    Beat::new("burn-in: heat and voltage", BEAT_MS)
        .note(
            "Burn-in holds parts at high temperature and raised voltage for hours, so weak parts fail in the factory instead of in a data center. Failure rates rise with temperature (Arrhenius), so heat speeds up the wear that would otherwise show later.",
            "The oven racks glow orange, heat rises off the top of the oven, and a part rides the overhead rail into the oven. The glass door shows the racks inside.",
        )
        .detail(
            "Heat and voltage age the part fast.",
            &["Hours at high temperature and raised voltage", "Standard for auto, medical and defense parts", "Increasingly used for AI chips"],
        ),
    Beat::new("system test: a real board", BEAT_MS)
        .note(
            "System-level test puts the packaged chip on a board that looks like the real product, boots software and runs a workload. It catches faults that structural patterns miss, such as software interaction, timing variability and thermal stress.",
            "A part docks on a system test board with a heat sink on its chip. The monitor beside it shows a workload as bars rising and falling.",
        )
        .detail(
            "It runs the chip the way it will be used.",
            &["Real-looking board, real software", "Catches faults that patterns miss", "Started with phone and PC chips; now AI accelerators"],
        ),
    Beat::new("speed bins by fmax", BEAT_MS)
        .note(
            "Every die is a little different. Test raises the clock until the part fails, which gives its maximum frequency, and parts are graded into bins by that speed. Faster bins sell at a premium, so one design gives several products.",
            "Parts drop from the rail into four bins, from the fastest green bin to the red scrap bin. Above them, a bell curve of maximum speeds lights up: most parts in the middle, a few at each end.",
        )
        .detail(
            "One design, several products.",
            &["Parts differ in maximum frequency (fmax)", "Clock raised until the part fails", "Faster bins sell at a premium"],
        ),
    Beat::new("sorted, then shipped", BEAT_MS)
        .note(
            "The handler sorts each part by its result into trays or tape and reel. Good parts go on to the customers who build boards and servers from them; parts that fail are sorted out and do not ship.",
            "The parts drop off the rail onto a pallet of sealed trays. The pallet is the last thing in the line, with the rail running on above it.",
        )
        .detail(
            "Each part leaves with a grade.",
            &["Sorted into trays or tape and reel", "Failed parts are sorted out, not shipped"],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_captioned() {
        let s = build();
        assert_eq!(s.beats().len(), 7);
        super::super::super::blender::explained(s.as_ref(), "FINAL TEST overview");
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "FINAL TEST overview");
    }
}
